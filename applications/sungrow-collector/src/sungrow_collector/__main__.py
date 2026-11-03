import argparse
import logging
import os
import sys
from collections.abc import Sequence
from datetime import date

from dotenv import load_dotenv

from sungrow_collector.client import ReauthorizationRequired, SungrowClient, SungrowError, extract_code
from sungrow_collector.collect import Collector, run_forever
from sungrow_collector.config import ConfigError, Settings, load_settings
from sungrow_collector.storage import StorageError, create_db_engine, reflect_readings_table
from sungrow_collector.tokens import TokenStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sungrow-collector")
    commands = parser.add_subparsers(dest="command", required=True)
    authorize = commands.add_parser(
        "authorize", help="exchange the OAuth code (or the full redirect URL) for tokens"
    )
    authorize.add_argument("code")
    poll = commands.add_parser("poll", help="read the inverter every POLL_INTERVAL_SECONDS")
    poll.add_argument("--once", action="store_true", help="read a single time and exit")
    backfill = commands.add_parser("backfill", help="load 5-minute history for past days")
    backfill.add_argument("--start", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    backfill.add_argument("--end", type=date.fromisoformat, required=True, help="YYYY-MM-DD")
    return parser


def _build_collector(settings: Settings, client: SungrowClient) -> Collector:
    assert settings.database_url is not None
    engine = create_db_engine(settings.database_url)
    return Collector(settings, client, engine, reflect_readings_table(engine))


def main(argv: Sequence[str] | None = None) -> int:
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    args = _parser().parse_args(argv)
    try:
        settings = load_settings(os.environ, need_database=args.command != "authorize")
        client = SungrowClient(settings, TokenStore(settings.token_file))
        if args.command == "authorize":
            tokens = client.exchange_code(extract_code(args.code))
            plants = ", ".join(tokens.ps_ids) or "none"
            print(f"tokens saved to {settings.token_file}; authorized plants: {plants}")
            return 0
        collector = _build_collector(settings, client)
        if args.command == "backfill":
            print(f"stored {collector.backfill(args.start, args.end)} readings")
        elif args.once:
            print(f"stored {collector.poll_once()} readings")
        else:
            run_forever(collector, settings.poll_interval_seconds)
    except (ConfigError, StorageError, ReauthorizationRequired, SungrowError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
