---
title: 'Interni podaci izdavača - kontakt osobe, Crossref kredencijali i napomene'
slug: 'publisher-internal-data'
created: '2026-03-15'
status: 'in-progress'
stepsCompleted: [1]
tech_stack: ['Django 5.x', 'Alpine.js', 'Bootstrap 5', 'django-fernet-fields']
files_to_modify: []
code_patterns: []
test_patterns: []
---

# Tech-Spec: Interni podaci izdavača - kontakt osobe, Crossref kredencijali i napomene

**Created:** 2026-03-15

## Overview

### Problem Statement

Admin korisnici DOI portala nemaju interni pregled kontakt osoba, Crossref kredencijala i napomena za izdavače unutar samog portala - koriste Excel tabelu za evidenciju tih podataka. Potrebno je centralizovati te interne informacije u portal, ali ih ne prikazivati na javnim stranicama.

### Solution

Proširiti Publisher model sa Crossref kredencijalima (username + enkriptovani password) i dodati tri nova child modela: PublisherContact (kontakt osobe), PublisherNote (napomene/komentari). Svi novi podaci su vidljivi isključivo u dashboard-u za Administrator/Superadmin korisnike.

### Scope

**In Scope:**
- `PublisherContact` child model sa soft delete (ime, prezime, email, telefon, role kao slobodan tekst)
- `crossref_username` i `crossref_password` (enkriptovano, opciono) na Publisher modelu
- `PublisherNote` child model - comment sekcija na publisher detail stranici (tekst, autor, created_at, updated_at)
- Inline formset + Alpine.js za kontakt osobe u publisher formi
- Password toggle (prikaži/sakrij) u dashboard UI-u
- Dodavanje `django-fernet-fields` biblioteke za enkriptovanje

**Out of Scope:**
- Promene na public stranicama (portal/ templates)
- Promene na postojećim `contact_email`/`contact_phone`/`website` poljima
- API/serializers za nove podatke
- Promene na RBAC sistemu (postojeći AdministratorRequiredMixin je dovoljan)

## Context for Development

### Codebase Patterns

{codebase_patterns}

### Files to Reference

| File | Purpose |
| ---- | ------- |

{files_table}

### Technical Decisions

{technical_decisions}

## Implementation Plan

### Tasks

{tasks}

### Acceptance Criteria

{acceptance_criteria}

## Additional Context

### Dependencies

{dependencies}

### Testing Strategy

{testing_strategy}

### Notes

{notes}
