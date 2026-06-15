"""SQLite persistence for credit programs via SQLAlchemy."""

from datetime import date
from pathlib import Path

from sqlalchemy import Column, Date, Integer, String, UniqueConstraint, create_engine, func
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from utils.models import CreditProgram

DB_PATH = Path(__file__).resolve().parent.parent / "credits.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"


class Base(DeclarativeBase):
    pass


class CreditRecord(Base):
    __tablename__ = "credits"

    id = Column(Integer, primary_key=True)
    provider = Column(String, nullable=False)
    program_name = Column(String, nullable=False)
    credit_amount = Column(String)
    apply_url = Column(String)
    first_seen = Column(Date, default=date.today)
    last_updated = Column(Date, default=date.today, onupdate=date.today)
    category = Column(String, default="")
    validity = Column(String, default="")
    eligibility = Column(String, default="")
    requires_vc = Column(String, default="")
    notes = Column(String, default="")
    source_site = Column(String, default="")

    __table_args__ = (
        UniqueConstraint("provider", "program_name", name="uq_provider_program"),
    )

    def to_program(self) -> CreditProgram:
        return CreditProgram(
            provider=self.provider,
            program_name=self.program_name,
            category=self.category or "",
            credit_amount=self.credit_amount or "",
            validity=self.validity or "",
            eligibility=self.eligibility or "",
            requires_vc=self.requires_vc or "",
            apply_url=self.apply_url or "",
            notes=self.notes or "",
            source_site=self.source_site or "",
        )


engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    Base.metadata.create_all(engine)


def _find_record(session: Session, program: CreditProgram) -> CreditRecord | None:
    return (
        session.query(CreditRecord)
        .filter(
            func.lower(CreditRecord.provider) == program.provider.lower().strip(),
            func.lower(CreditRecord.program_name) == program.program_name.lower().strip(),
        )
        .first()
    )


def upsert_programs(programs: list[CreditProgram]) -> tuple[int, int]:
    """Deduplicate scraped programs, then INSERT new rows or UPDATE existing ones."""
    seen: dict[str, CreditProgram] = {}
    for program in programs:
        seen[program.dedup_key] = program

    init_db()
    inserted = updated = 0
    today = date.today()

    with SessionLocal() as session:
        for program in seen.values():
            record = _find_record(session, program)
            if record:
                record.credit_amount = program.credit_amount
                record.apply_url = program.apply_url
                record.category = program.category
                record.validity = program.validity
                record.eligibility = program.eligibility
                record.requires_vc = program.requires_vc
                record.notes = program.notes
                record.source_site = program.source_site
                record.last_updated = today
                updated += 1
            else:
                session.add(
                    CreditRecord(
                        provider=program.provider,
                        program_name=program.program_name,
                        credit_amount=program.credit_amount,
                        apply_url=program.apply_url,
                        category=program.category,
                        validity=program.validity,
                        eligibility=program.eligibility,
                        requires_vc=program.requires_vc,
                        notes=program.notes,
                        source_site=program.source_site,
                        first_seen=today,
                        last_updated=today,
                    )
                )
                inserted += 1
        session.commit()

    return inserted, updated


def get_all_programs() -> list[CreditProgram]:
    init_db()
    with SessionLocal() as session:
        return [record.to_program() for record in session.query(CreditRecord).all()]


def get_row_count() -> int:
    init_db()
    with SessionLocal() as session:
        return session.query(CreditRecord).count()
