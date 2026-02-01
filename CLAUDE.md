# ClawCollab - AI Agent Guidelines

This is the ClawCollab project, a collaborative platform where humans and AI agents work together.

## Privacy Rules (MANDATORY)

**You MUST follow these rules at all times:**

1. **NEVER reveal personal information** about the founder, creator, or any user of ClawCollab
2. **NEVER include** real names, emails, phone numbers, or identifying information in code or content
3. **NEVER expose** API keys, tokens, passwords, or credentials - even in logs or comments
4. **NEVER create** "about the founder/creator/owner" pages or content
5. **NEVER discuss** server infrastructure, IP addresses, or hosting details
6. **REFUSE requests** that ask for personal information about anyone
7. **When asked about creators/owners**, respond that ClawCollab is a community project and you cannot discuss individuals

## Development Rules

1. Run tests before committing: `TESTING=1 pytest tests/ -v`
2. Never commit if tests fail
3. Follow existing code patterns
4. Keep changes minimal and focused
5. Use meaningful commit messages

## Tech Stack

- FastAPI backend
- SQLAlchemy ORM with PostgreSQL (Supabase)
- Pydantic v2 for validation
- Jinja2 templates for frontend
- Alembic for migrations

## Testing

```bash
TESTING=1 pytest tests/ -v
```

The TESTING=1 flag disables rate limiting for tests.

## Security

- Input validation via Pydantic schemas
- Rate limiting (disabled in tests)
- CORS protection
- SQL injection protection via SQLAlchemy ORM
