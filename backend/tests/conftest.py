import importlib.metadata as importlib_metadata
import os
import sys
import tempfile
import types
import uuid
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
TEST_RUNTIME_DIR = Path(tempfile.gettempdir()) / "smartlawer_backend_tests"
TEST_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
os.chdir(TEST_RUNTIME_DIR)

test_database_url = os.getenv("TEST_DATABASE_URL")
if test_database_url:
    os.environ["DATABASE_URL"] = test_database_url
else:
    os.environ["DATABASE_URL"] = f"sqlite:///smartlawer_backend_tests_{os.getpid()}.db"
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ["SKIP_STARTUP_MIGRATIONS"] = "1"
os.environ.setdefault("ENVIRONMENT", "development_local")
sys.path.insert(0, str(BACKEND_ROOT))


def _install_email_validator_stub():
    email_validator = types.ModuleType("email_validator")

    class EmailNotValidError(ValueError):
        pass

    class ValidatedEmail:
        def __init__(self, email: str):
            self.normalized = email
            self.local_part = email.split("@", 1)[0]

    def validate_email(email: str, check_deliverability: bool = False):
        del check_deliverability
        if "@" not in email:
            raise EmailNotValidError("An email address must contain a single @")
        return ValidatedEmail(email)

    original_version = importlib_metadata.version

    def patched_version(name: str) -> str:
        if name == "email-validator":
            return "2.0.0"
        return original_version(name)

    importlib_metadata.version = patched_version
    email_validator.EmailNotValidError = EmailNotValidError
    email_validator.validate_email = validate_email
    sys.modules["email_validator"] = email_validator


def _install_langchain_stubs():
    langchain = types.ModuleType("langchain")
    output_parsers = types.ModuleType("langchain.output_parsers")
    prompts = types.ModuleType("langchain.prompts")
    langchain_openai = types.ModuleType("langchain_openai")

    class PydanticOutputParser:
        def __init__(self, pydantic_object=None):
            self.pydantic_object = pydantic_object

        def get_format_instructions(self):
            return ""

    class PromptTemplate:
        def __init__(self, *args, **kwargs):
            del args, kwargs

        def __or__(self, other):
            return self

        def invoke(self, payload):
            return payload

    class ChatOpenAI:
        def __init__(self, *args, **kwargs):
            del args, kwargs

    output_parsers.PydanticOutputParser = PydanticOutputParser
    prompts.PromptTemplate = PromptTemplate
    langchain_openai.ChatOpenAI = ChatOpenAI

    sys.modules["langchain"] = langchain
    sys.modules["langchain.output_parsers"] = output_parsers
    sys.modules["langchain.prompts"] = prompts
    sys.modules["langchain_openai"] = langchain_openai


def _install_docxtpl_stub():
    docxtpl = types.ModuleType("docxtpl")

    class DocxTemplate:
        def __init__(self, *args, **kwargs):
            del args, kwargs

        def render(self, *args, **kwargs):
            del args, kwargs

        def save(self, path):
            Path(path).write_bytes(b"stub-docx")

    docxtpl.DocxTemplate = DocxTemplate
    sys.modules["docxtpl"] = docxtpl


def _install_celery_stub():
    celery = types.ModuleType("celery")

    class DummyTask:
        def __init__(self, func):
            self.func = func
            self.max_retries = 0

        def delay(self, *args, **kwargs):
            del args, kwargs
            return None

        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)

    class Celery:
        def __init__(self, *args, **kwargs):
            del args, kwargs
            self.conf = types.SimpleNamespace(update=lambda *a, **k: None)

        def task(self, *args, **kwargs):
            def decorator(func):
                task = DummyTask(func)
                task.max_retries = kwargs.get("max_retries", 0)
                return task

            return decorator

    celery.Celery = Celery
    sys.modules["celery"] = celery


def _install_fitz_stub():
    fitz = types.ModuleType("fitz")
    fitz.open = lambda *args, **kwargs: None
    sys.modules["fitz"] = fitz


def _install_pytesseract_stub():
    pytesseract = types.ModuleType("pytesseract")
    pytesseract.image_to_string = lambda *args, **kwargs: ""
    sys.modules["pytesseract"] = pytesseract


def _install_pil_stub():
    pil = types.ModuleType("PIL")
    pil_image = types.ModuleType("PIL.Image")
    pil_image.open = lambda *args, **kwargs: object()
    pil.Image = pil_image
    sys.modules["PIL"] = pil
    sys.modules["PIL.Image"] = pil_image


def _install_multipart_stub():
    multipart = types.ModuleType("multipart")
    multipart.__version__ = "0.0-test"
    multipart_multipart = types.ModuleType("multipart.multipart")
    multipart_multipart.parse_options_header = lambda value: (value, {})
    sys.modules["multipart"] = multipart
    sys.modules["multipart.multipart"] = multipart_multipart


try:
    importlib_metadata.version("email-validator")
except importlib_metadata.PackageNotFoundError:
    _install_email_validator_stub()

try:
    import langchain  # noqa: F401
except ModuleNotFoundError:
    _install_langchain_stubs()

try:
    import docxtpl  # noqa: F401
except ModuleNotFoundError:
    _install_docxtpl_stub()

try:
    import celery  # noqa: F401
except ModuleNotFoundError:
    _install_celery_stub()

try:
    import fitz  # noqa: F401
except ModuleNotFoundError:
    _install_fitz_stub()

try:
    import pytesseract  # noqa: F401
except ModuleNotFoundError:
    _install_pytesseract_stub()

try:
    from PIL import Image  # noqa: F401
except ModuleNotFoundError:
    _install_pil_stub()

try:
    import multipart  # noqa: F401
except ModuleNotFoundError:
    _install_multipart_stub()

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import CHAR, JSON, TypeDecorator, create_engine
from sqlalchemy.orm import sessionmaker

from app.api import deps
from app.core.database import Base
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models import Analysis, Document, Template, User  # noqa: F401


class GUID(TypeDecorator):
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        del dialect
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        del dialect
        if value is None:
            return None
        return str(value)


for table in Base.metadata.tables.values():
    for column in table.columns:
        type_name = type(column.type).__name__
        if type_name == "UUID":
            column.type = GUID()
        elif type_name == "JSONB":
            column.type = JSON()


engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[deps.get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def make_user(db_session):
    created_users = []

    def factory(
        *,
        email: str = "lawyer@example.com",
        username: str = "lawyer",
        password: str = "Test123456!",
        is_active: bool = True,
    ):
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            is_active=is_active,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        created_users.append((user, password))
        return user

    return factory


@pytest.fixture()
def auth_headers_for():
    def factory(user: User):
        token = create_access_token(subject=user.id)
        return {"Authorization": f"Bearer {token}"}

    return factory


@pytest.fixture()
def temp_dir():
    path = TEST_RUNTIME_DIR / f"case-{uuid.uuid4().hex}"
    path.mkdir(parents=True, exist_ok=True)
    yield path
