#!/usr/bin/env python3
"""
Script to add admin user to the database.
Usage: python add_admin.py
"""

import os
import sys
from app import create_app, db
from app.models import User, Sponsor


def add_admin_user():
    """Add admin user to database."""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if user already exists
            existing_user = User.get_by_email('miiihaaas@gmail.com')
            if existing_user:
                print(f"User {existing_user.email} već postoji u bazi!")
                print(f"Role: {existing_user.role}")
                print(f"Full name: {existing_user.full_name}")
                return
            
            # Create admin user
            admin_user = User.create_user(
                email='miiihaaas@gmail.com',
                password='testiram',
                full_name='Mihailo Admin',
                role='admin'
            )
            
            print("Admin korisnik uspešno kreiran:")
            print(f"   Email: {admin_user.email}")
            print(f"   Role: {admin_user.role}")
            print(f"   Full name: {admin_user.full_name}")
            print(f"   ID: {admin_user.id}")
            
            # Also show sponsor info if exists
            sponsor = Sponsor.get_instance()
            if sponsor:
                print("\nSponsor organizacija:")
                print(f"   Name: {sponsor.name}")
                print(f"   Email: {sponsor.email}")
                print(f"   Crossref ID: {sponsor.crossref_member_id}")
                print(f"   Active: {sponsor.is_active}")
            else:
                print("\nNapomena: Nema sponsor organizacije u bazi!")
                
        except Exception as e:
            print(f"Greška pri kreiranju admin korisnika: {e}")
            sys.exit(1)


if __name__ == '__main__':
    add_admin_user()