"""
Views for Conference Registration Wizard.

Task 4: Step 1 (Conference/Publication)
Task 5: Step 2 (Proceedings/Issue)
Task 6: Step 3 (Papers/Articles)
Task 7: Author wrapper endpoints
Task 8: Step 4 (Review & XML generation)
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST, require_http_methods

from doi_portal.articles.forms import AuthorForm
from doi_portal.articles.models import (
    Article,
    ArticleStatus,
    Author,
    AuthorSequence,
)
from doi_portal.crossref.services import CrossrefService, PreValidationService
from doi_portal.crossref.validation import ValidationResult
from doi_portal.issues.models import Issue
from doi_portal.publications.models import Publication, PublicationType

from .forms import WizardConferenceForm, WizardPaperForm, WizardProceedingsForm


# =============================================================================
# Permission helper
# =============================================================================


def _check_wizard_permission(user, publication):
    """Check user has access to publication's publisher."""
    if user.is_superuser:
        return
    if user.groups.filter(name__in=["Administrator", "Superadmin"]).exists():
        return
    if hasattr(user, "publisher") and user.publisher == publication.publisher:
        return
    raise PermissionDenied


def _check_article_permission(user, article):
    """Check user has permission to modify this article."""
    if user.is_superuser:
        return
    if user.groups.filter(name__in=["Administrator", "Superadmin"]).exists():
        return
    if hasattr(user, "publisher") and user.publisher:
        if article.issue.publication.publisher == user.publisher:
            return
    raise PermissionDenied


def _get_wizard_context(publication, current_step):
    """Build common wizard context."""
    issue = Issue.objects.filter(publication=publication).first()
    max_completed = 0
    if publication.pk:
        max_completed = 1
    if issue:
        max_completed = 2
        if issue.articles.filter(is_deleted=False).exists():
            max_completed = 3

    return {
        "publication": publication,
        "issue": issue,
        "current_step": current_step,
        "max_completed_step": max_completed,
        "steps": [
            {"number": 1, "label": "Konferencija", "icon": "bi-megaphone"},
            {"number": 2, "label": "Zbornik", "icon": "bi-journal-text"},
            {"number": 3, "label": "Radovi", "icon": "bi-file-earmark-text"},
            {"number": 4, "label": "Pregled", "icon": "bi-check-circle"},
        ],
    }


# =============================================================================
# Task 4: Step 1 - Conference (Publication)
# =============================================================================


@login_required
@require_http_methods(["GET", "POST"])
def wizard_start(request):
    """
    Start wizard: GET=empty form, POST=create Publication + redirect to step-2.

    Merged start + step-1 to prevent orphans from double-click.
    """
    user = request.user

    # Permission check: user must have publisher or be admin
    if not user.is_superuser and not user.groups.filter(
        name__in=["Administrator", "Superadmin"]
    ).exists():
        if not (hasattr(user, "publisher") and user.publisher):
            raise PermissionDenied

    if request.method == "POST":
        form = WizardConferenceForm(request.POST, user=user)
        if form.is_valid():
            publication = form.save()
            return redirect("wizard:conference-step-2", pub_pk=publication.pk)
    else:
        form = WizardConferenceForm(user=user)

    context = {
        "form": form,
        "current_step": 1,
        "max_completed_step": 0,
        "is_create": True,
        "steps": [
            {"number": 1, "label": "Konferencija", "icon": "bi-megaphone"},
            {"number": 2, "label": "Zbornik", "icon": "bi-journal-text"},
            {"number": 3, "label": "Radovi", "icon": "bi-file-earmark-text"},
            {"number": 4, "label": "Pregled", "icon": "bi-check-circle"},
        ],
        "breadcrumbs": [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "Registracija konferencije", "url": None},
        ],
    }
    return render(request, "wizard/conference_wizard.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def wizard_step_1(request, pub_pk):
    """Step 1 edit mode (back navigation from step 2+)."""
    publication = get_object_or_404(Publication, pk=pub_pk)
    _check_wizard_permission(request.user, publication)

    if request.method == "POST":
        form = WizardConferenceForm(request.POST, instance=publication, user=request.user)
        if form.is_valid():
            form.save()
            return redirect("wizard:conference-step-2", pub_pk=publication.pk)
    else:
        form = WizardConferenceForm(instance=publication, user=request.user)

    context = _get_wizard_context(publication, current_step=1)
    context.update({
        "form": form,
        "is_create": False,
        "breadcrumbs": [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "Registracija konferencije", "url": None},
            {"label": "Konferencija", "url": None},
        ],
    })
    return render(request, "wizard/conference_wizard.html", context)


# =============================================================================
# Task 5: Step 2 - Proceedings (Issue)
# =============================================================================


@login_required
@require_http_methods(["GET", "POST"])
def wizard_step_2(request, pub_pk):
    """Step 2: Proceedings (Issue) creation/editing."""
    publication = get_object_or_404(
        Publication.objects.select_related("publisher"), pk=pub_pk
    )
    _check_wizard_permission(request.user, publication)

    issue = Issue.objects.filter(publication=publication).first()

    if request.method == "POST":
        form = WizardProceedingsForm(
            request.POST,
            instance=issue,
            publication=publication,
        )
        if form.is_valid():
            form.save()
            return redirect("wizard:conference-step-3", pub_pk=publication.pk)
    else:
        form = WizardProceedingsForm(
            instance=issue,
            publication=publication,
        )

    context = _get_wizard_context(publication, current_step=2)
    context.update({
        "form": form,
        "breadcrumbs": [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "Registracija konferencije", "url": None},
            {"label": "Zbornik", "url": None},
        ],
    })
    return render(request, "wizard/conference_wizard.html", context)


# =============================================================================
# Task 6: Step 3 - Papers (Articles)
# =============================================================================


@login_required
@require_http_methods(["GET"])
def wizard_step_3(request, pub_pk):
    """Step 3: Papers list with HTMX CRUD."""
    publication = get_object_or_404(Publication, pk=pub_pk)
    _check_wizard_permission(request.user, publication)

    issue = get_object_or_404(Issue, publication=publication)
    articles = (
        issue.articles.filter(is_deleted=False)
        .prefetch_related("authors__affiliations")
        .order_by("pk")
    )

    context = _get_wizard_context(publication, current_step=3)
    context.update({
        "articles": articles,
        "breadcrumbs": [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "Registracija konferencije", "url": None},
            {"label": "Radovi", "url": None},
        ],
    })
    return render(request, "wizard/conference_wizard.html", context)


@login_required
@require_http_methods(["GET", "POST"])
def wizard_paper_add(request, pub_pk):
    """Add a paper (Article) via HTMX."""
    publication = get_object_or_404(Publication, pk=pub_pk)
    _check_wizard_permission(request.user, publication)
    issue = get_object_or_404(Issue, publication=publication)

    if request.method == "POST":
        form = WizardPaperForm(request.POST, issue=issue, user=request.user)
        if form.is_valid():
            form.save()
            articles = (
                issue.articles.filter(is_deleted=False)
                .prefetch_related("authors__affiliations")
                .order_by("pk")
            )
            return render(request, "wizard/partials/_paper_list.html", {
                "articles": articles,
                "publication": publication,
                "issue": issue,
            })
    else:
        form = WizardPaperForm(issue=issue, user=request.user)

    return render(request, "wizard/partials/_paper_form.html", {
        "form": form,
        "publication": publication,
        "issue": issue,
    })


@login_required
@require_http_methods(["GET", "POST"])
def wizard_paper_edit(request, pub_pk, article_pk):
    """Edit a paper (Article) via HTMX."""
    publication = get_object_or_404(Publication, pk=pub_pk)
    _check_wizard_permission(request.user, publication)
    issue = get_object_or_404(Issue, publication=publication)
    article = get_object_or_404(Article, pk=article_pk, issue=issue, is_deleted=False)

    if request.method == "POST":
        form = WizardPaperForm(request.POST, instance=article, issue=issue, user=request.user)
        if form.is_valid():
            form.save()
            articles = (
                issue.articles.filter(is_deleted=False)
                .prefetch_related("authors__affiliations")
                .order_by("pk")
            )
            return render(request, "wizard/partials/_paper_list.html", {
                "articles": articles,
                "publication": publication,
                "issue": issue,
            })
    else:
        form = WizardPaperForm(instance=article, issue=issue, user=request.user)

    return render(request, "wizard/partials/_paper_form.html", {
        "form": form,
        "publication": publication,
        "issue": issue,
        "article": article,
    })


@login_required
@require_POST
def wizard_paper_delete(request, pub_pk, article_pk):
    """Delete a paper (Article) via HTMX - hard delete for DRAFT wizard articles."""
    publication = get_object_or_404(Publication, pk=pub_pk)
    _check_wizard_permission(request.user, publication)
    issue = get_object_or_404(Issue, publication=publication)
    article = get_object_or_404(Article, pk=article_pk, issue=issue, is_deleted=False)

    article.delete()

    articles = (
        issue.articles.filter(is_deleted=False)
        .prefetch_related("authors__affiliations")
        .order_by("pk")
    )
    return render(request, "wizard/partials/_paper_list.html", {
        "articles": articles,
        "publication": publication,
        "issue": issue,
    })


# =============================================================================
# Task 7: Wizard author wrapper endpoints
# =============================================================================


@login_required
def wizard_author_list(request, article_pk):
    """Return wizard-specific author list partial for an article."""
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=article_pk,
    )
    _check_article_permission(request.user, article)
    authors = article.authors.prefetch_related("affiliations").all()
    return render(request, "wizard/partials/_wizard_author_list.html", {
        "article": article,
        "authors": authors,
    })


@login_required
def wizard_author_form(request, article_pk):
    """Return empty wizard-specific author form partial."""
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=article_pk,
    )
    _check_article_permission(request.user, article)
    return render(request, "wizard/partials/_wizard_author_form.html", {
        "author_form": AuthorForm(),
        "article": article,
    })


@login_required
@require_POST
def wizard_author_add(request, article_pk):
    """Add author to article, return wizard-specific partial."""
    article = get_object_or_404(
        Article.objects.select_related(
            "issue", "issue__publication", "issue__publication__publisher"
        ),
        pk=article_pk,
    )
    _check_article_permission(request.user, article)

    form = AuthorForm(request.POST)
    if form.is_valid():
        author = form.save(commit=False)
        author.article = article
        max_order = article.authors.aggregate(
            max_order=models.Max("order")
        )["max_order"] or 0
        author.order = max_order + 1
        author.sequence = AuthorSequence.FIRST if author.order == 1 else AuthorSequence.ADDITIONAL
        author.save()
        authors = article.authors.prefetch_related("affiliations").all()
        return render(request, "wizard/partials/_wizard_author_list.html", {
            "article": article,
            "authors": authors,
        })

    # Return form with errors
    response = render(request, "wizard/partials/_wizard_author_form.html", {
        "author_form": form,
        "article": article,
    })
    response["HX-Retarget"] = f"#wizard-author-form-{article.pk}"
    response["HX-Reswap"] = "innerHTML"
    return response


@login_required
def wizard_author_edit_form(request, pk):
    """Return pre-filled wizard author form for editing."""
    author = get_object_or_404(
        Author.objects.select_related(
            "article", "article__issue",
            "article__issue__publication",
            "article__issue__publication__publisher",
        ),
        pk=pk,
    )
    _check_article_permission(request.user, author.article)
    return render(request, "wizard/partials/_wizard_author_form.html", {
        "author_form": AuthorForm(instance=author),
        "article": author.article,
        "author": author,
    })


@login_required
@require_POST
def wizard_author_update(request, pk):
    """Update author, return wizard-specific partial."""
    author = get_object_or_404(
        Author.objects.select_related(
            "article", "article__issue",
            "article__issue__publication",
            "article__issue__publication__publisher",
        ),
        pk=pk,
    )
    _check_article_permission(request.user, author.article)

    form = AuthorForm(request.POST, instance=author)
    if form.is_valid():
        form.save()
    else:
        response = render(request, "wizard/partials/_wizard_author_form.html", {
            "author_form": form,
            "article": author.article,
            "author": author,
        })
        response["HX-Retarget"] = f"#wizard-author-form-{author.article.pk}"
        response["HX-Reswap"] = "innerHTML"
        return response

    article = author.article
    authors = article.authors.prefetch_related("affiliations").all()
    return render(request, "wizard/partials/_wizard_author_list.html", {
        "article": article,
        "authors": authors,
    })


@login_required
@require_POST
def wizard_author_delete(request, pk):
    """Delete author, re-order remaining, return wizard-specific partial."""
    author = get_object_or_404(
        Author.objects.select_related(
            "article", "article__issue",
            "article__issue__publication",
            "article__issue__publication__publisher",
        ),
        pk=pk,
    )
    _check_article_permission(request.user, author.article)

    article = author.article
    author.delete()

    # Re-order remaining authors and recalculate sequence
    remaining = article.authors.order_by("order")
    for index, a in enumerate(remaining, start=1):
        Author.objects.filter(pk=a.pk).update(
            order=index,
            sequence=AuthorSequence.FIRST if index == 1 else AuthorSequence.ADDITIONAL,
        )

    authors = article.authors.prefetch_related("affiliations").all()
    return render(request, "wizard/partials/_wizard_author_list.html", {
        "article": article,
        "authors": authors,
    })


# =============================================================================
# Task 8: Step 4 - Review & XML generation
# =============================================================================


def wizard_validate_issue(issue):
    """
    Validate issue for wizard - includes DRAFT articles (not just PUBLISHED).

    Uses PreValidationService internal methods directly.
    """
    service = PreValidationService()
    result = ValidationResult()

    # Standard validations (depositor, type-specific fields)
    result.merge(service._validate_depositor_settings())
    result.merge(service._validate_conference_fields(issue))
    result.merge(service._validate_issue_doi_suffix(issue))

    # Validate ALL articles (not just PUBLISHED) - this is the key difference
    articles = issue.articles.filter(is_deleted=False)
    if not articles.exists():
        result.add_error(
            message="Nema radova za generisanje XML-a.",
            field_name="articles",
        )
    for article in articles:
        result.merge(service._validate_article(article))

    return result


@login_required
@require_http_methods(["GET"])
def wizard_step_4(request, pub_pk):
    """Step 4: Review summary + validation + generate XML button."""
    publication = get_object_or_404(
        Publication.objects.select_related("publisher"), pk=pub_pk
    )
    _check_wizard_permission(request.user, publication)

    issue = get_object_or_404(
        Issue.objects.select_related("publication", "publication__publisher"),
        publication=publication,
    )
    articles = (
        issue.articles.filter(is_deleted=False)
        .prefetch_related("authors__affiliations")
        .order_by("pk")
    )

    validation_result = wizard_validate_issue(issue)

    context = _get_wizard_context(publication, current_step=4)
    context.update({
        "articles": articles,
        "validation_result": validation_result,
        "has_errors": validation_result.has_errors(),
        "breadcrumbs": [
            {"label": "Kontrolna tabla", "url": "dashboard"},
            {"label": "Registracija konferencije", "url": None},
            {"label": "Pregled", "url": None},
        ],
    })
    return render(request, "wizard/conference_wizard.html", context)


@login_required
@require_POST
def wizard_generate_xml(request, pub_pk):
    """Generate XML: transition DRAFT->PUBLISHED, generate XML, redirect to deposit."""
    publication = get_object_or_404(Publication, pk=pub_pk)
    _check_wizard_permission(request.user, publication)

    issue = get_object_or_404(Issue, publication=publication)

    # Step 1: Transition DRAFT -> PUBLISHED
    issue.articles.filter(
        status=ArticleStatus.DRAFT, is_deleted=False
    ).update(status=ArticleStatus.PUBLISHED)

    # Step 2: Generate XML
    service = CrossrefService()
    service.generate_and_store_xml(issue)

    # Step 3: Redirect to crossref deposit workflow
    return redirect("crossref:issue-deposit", pk=issue.pk)
