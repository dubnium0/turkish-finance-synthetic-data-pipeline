"""Command-line interface for the Finetool-TR curation pipeline."""

from __future__ import annotations

import argparse
import json

from . import pipeline
from .models import CandidateStatus
from .settings import load_settings


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser("tcg", description="Türkçe finans tool-call veri hattı")
    parser.add_argument("-c", "--config", default="config.yaml")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Şemaları ve katalogu doğrula; yerel durumu başlat")

    ingest_cmd = commands.add_parser("ingest", help="Sabitlenmiş instruction kaynağını içeri al")
    ingest_cmd.add_argument("--limit", type=int)

    build_cmd = commands.add_parser("build", help="Kaynaklardan sade aday kayıtlar üret")
    build_cmd.add_argument("--limit", type=int)
    build_cmd.add_argument("--no-seeds", action="store_true")

    commands.add_parser("validate", help="Pydantic ve JSON Schema kapılarını çalıştır")

    review_cmd = commands.add_parser("review", help="Adayları insan incelemesi için listele")
    review_cmd.add_argument(
        "--status", choices=[status.value for status in CandidateStatus], default="valid"
    )
    review_cmd.add_argument("--source")
    review_cmd.add_argument("--limit", type=int, default=20)

    approve_cmd = commands.add_parser("approve", help="İncelenmiş geçerli adayları kabul et")
    approve_cmd.add_argument("ids", nargs="*")
    approve_cmd.add_argument("--all-valid", action="store_true")
    approve_cmd.add_argument("--source")
    approve_cmd.add_argument("--limit", type=int)

    reject_cmd = commands.add_parser("reject", help="Aday kimliklerini reddet")
    reject_cmd.add_argument("ids", nargs="+")

    commands.add_parser("export", help="Sadece kabul edilen üç alanlı kayıtları dışa aktar")
    commands.add_parser("report", help="Durum ve davranış dağılımını göster")

    args = parser.parse_args(argv)
    settings = load_settings(args.config)

    if args.command == "init":
        _print(pipeline.initialize(settings))
    elif args.command == "ingest":
        _print({"ingested": pipeline.ingest(settings, args.limit)})
    elif args.command == "build":
        _print({"built": pipeline.build(settings, args.limit, not args.no_seeds)})
    elif args.command == "validate":
        _print(pipeline.validate(settings))
    elif args.command == "review":
        _print(
            pipeline.review(
                settings,
                status=CandidateStatus(args.status),
                source_id=args.source,
                limit=args.limit,
            )
        )
    elif args.command == "approve":
        selectors = int(args.all_valid) + int(bool(args.source)) + int(bool(args.ids))
        if selectors != 1:
            parser.error("approve için yalnızca bir ID listesi, --source veya --all-valid gerekli")
        _print(
            {
                "approved": pipeline.approve_valid(
                    settings,
                    args.limit,
                    source_id=args.source,
                    selected_ids=set(args.ids) if args.ids else None,
                )
            }
        )
    elif args.command == "reject":
        _print({"rejected": pipeline.reject(settings, args.ids)})
    elif args.command == "export":
        _print({"exported": pipeline.export(settings)})
    elif args.command == "report":
        _print(pipeline.report(settings))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
