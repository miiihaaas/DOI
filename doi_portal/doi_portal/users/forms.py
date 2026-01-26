from allauth.account.forms import SignupForm
from allauth.socialaccount.forms import SignupForm as SocialSignupForm
from django import forms
from django.contrib.auth import forms as admin_forms
from django.contrib.auth.models import Group
from django.forms import EmailField
from django.utils.translation import gettext_lazy as _

from .models import User
from .services import assign_publisher_permissions
from .services import remove_publisher_permissions

# Role choices for user management forms (Story 1.6)
ROLE_CHOICES = [
    ("Superadmin", "Superadmin"),
    ("Administrator", "Administrator"),
    ("Urednik", "Urednik"),
    ("Bibliotekar", "Bibliotekar"),
]


class UserAdminChangeForm(admin_forms.UserChangeForm):
    class Meta(admin_forms.UserChangeForm.Meta):  # type: ignore[name-defined]
        model = User
        field_classes = {"email": EmailField}


class UserAdminCreationForm(admin_forms.AdminUserCreationForm):
    """
    Form for User Creation in the Admin Area.
    To change user signup, see UserSignupForm and UserSocialSignupForm.
    """

    class Meta(admin_forms.UserCreationForm.Meta):  # type: ignore[name-defined]
        model = User
        fields = ("email",)
        field_classes = {"email": EmailField}
        error_messages = {
            "email": {"unique": _("This email has already been taken.")},
        }


class UserSignupForm(SignupForm):
    """
    Form that will be rendered on a user sign up section/screen.
    Default fields will be added automatically.
    Check UserSocialSignupForm for accounts created from social.
    """


class UserSocialSignupForm(SocialSignupForm):
    """
    Renders the form when user has signed up using social accounts.
    Default fields will be added automatically.
    See UserSignupForm otherwise.
    """


# ============================================================================
# Story 1.6: User Management Forms for Superadmin
# ============================================================================


class UserCreateForm(forms.ModelForm):
    """
    Form for creating new users by Superadmin (Story 1.6, AC#2, AC#3).

    Fields:
    - email: User's email address (required, unique)
    - name: User's display name
    - role: RBAC Group assignment
    - publisher: Optional publisher assignment for row-level permissions
    - password1/password2: Password fields (optional if send_invitation is True)
    - send_invitation: If True, user is created without password
    """

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label=_("Uloga"),
        help_text=_("Izaberite ulogu korisnika"),
    )

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        label=_("Lozinka"),
        required=False,
        help_text=_("Ostavite prazno ako saljete email pozivnicu"),
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        label=_("Potvrda lozinke"),
        required=False,
    )

    send_invitation = forms.BooleanField(
        required=False,
        label=_("Posalji email pozivnicu"),
        help_text=_("Korisnik ce postaviti lozinku putem email linka"),
    )

    class Meta:
        model = User
        fields = ["email", "name", "publisher"]
        labels = {
            "email": _("Email adresa"),
            "name": _("Ime i prezime"),
            "publisher": _("Izdavac"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make publisher optional with empty choice
        self.fields["publisher"].required = False
        self.fields["publisher"].empty_label = _("--- Bez dodele izdavaca ---")
        # Set email as required
        self.fields["email"].required = True

    def clean(self):
        cleaned_data = super().clean()
        send_invitation = cleaned_data.get("send_invitation")
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if not send_invitation:
            # Password is required if not sending invitation
            if not password1 or not password2:
                raise forms.ValidationError(
                    _("Lozinka je obavezna ako ne saljete email pozivnicu."),
                )
            if password1 != password2:
                raise forms.ValidationError(_("Lozinke se ne poklapaju."))
        return cleaned_data

    def save(self, commit: bool = True) -> User:  # noqa: FBT001, FBT002
        """
        Save user with role assignment and optional password.

        AC#3: Creates user with selected Group assignment and guardian permissions.
        """
        user = super().save(commit=False)

        # Set password or mark as unusable for invitation
        if not self.cleaned_data.get("send_invitation"):
            user.set_password(self.cleaned_data["password1"])
        else:
            user.set_unusable_password()

        if commit:
            user.save()
            # Assign role (Group)
            role_name = self.cleaned_data["role"]
            group = Group.objects.get(name=role_name)
            user.groups.add(group)

            # AC#3: Assign guardian permissions for publisher if set
            publisher = self.cleaned_data.get("publisher")
            if publisher:
                assign_publisher_permissions(user, publisher)

        return user


class UserUpdateForm(forms.ModelForm):
    """
    Form for updating existing users by Superadmin (Story 1.6, AC#4).

    Fields:
    - email: User's email address
    - name: User's display name
    - role: RBAC Group assignment (changing removes old groups)
    - publisher: Publisher assignment for row-level permissions
    """

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label=_("Uloga"),
        help_text=_("Promena uloge uklanja prethodne grupne clanstvo"),
    )

    class Meta:
        model = User
        fields = ["email", "name", "publisher"]
        labels = {
            "email": _("Email adresa"),
            "name": _("Ime i prezime"),
            "publisher": _("Izdavac"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make publisher optional with empty choice
        self.fields["publisher"].required = False
        self.fields["publisher"].empty_label = _("--- Bez dodele izdavaca ---")

        # Set initial role from user's current groups
        if self.instance and self.instance.pk:
            current_groups = self.instance.groups.filter(
                name__in=[choice[0] for choice in ROLE_CHOICES],
            )
            if current_groups.exists():
                self.initial["role"] = current_groups.first().name

    def save(self, commit: bool = True) -> User:  # noqa: FBT001, FBT002
        """
        Save user with role/publisher updates.

        AC#4: Updates Group membership when role changes and guardian permissions.
        """
        user = super().save(commit=False)

        # Track old publisher for permission updates
        old_publisher = None
        if user.pk:
            old_publisher = User.objects.get(pk=user.pk).publisher

        if commit:
            user.save()

            # Update role (Group membership)
            new_role_name = self.cleaned_data["role"]

            # Remove all RBAC groups first
            rbac_groups = Group.objects.filter(
                name__in=[choice[0] for choice in ROLE_CHOICES],
            )
            user.groups.remove(*rbac_groups)

            # Add new role group
            new_group = Group.objects.get(name=new_role_name)
            user.groups.add(new_group)

            # AC#4: Handle guardian permission changes when publisher changes
            new_publisher = self.cleaned_data.get("publisher")
            if old_publisher != new_publisher:
                # Remove old publisher permissions
                if old_publisher:
                    remove_publisher_permissions(user, old_publisher)
                # Assign new publisher permissions
                if new_publisher:
                    assign_publisher_permissions(user, new_publisher)

        return user
