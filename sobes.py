#!/usr/bin/env python3
"""Measure download speed by making sequential requests to a URL."""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_REQUESTS = 10
DEFAULT_TIMEOUT = 30.0
CHUNK_SIZE = 1024 * 1024


@dataclass(frozen=True)
class Measurement:
	elapsed_seconds: float
	downloaded_bytes: int


def download_once(url: str, timeout: float) -> Measurement:
	"""Download the complete response and return its duration and size."""
	request = Request(url, headers={"User-Agent": "sobes-speed-test/1.0"})
	started_at = time.perf_counter()
	downloaded_bytes = 0

	with urlopen(request, timeout=timeout) as response:
		while True:
			chunk = response.read(CHUNK_SIZE)
			if not chunk:
				break
			downloaded_bytes += len(chunk)

	return Measurement(time.perf_counter() - started_at, downloaded_bytes)


def format_bytes(value: float) -> str:
	"""Format bytes using decimal units suitable for network speed output."""
	return f"{value / 1_000_000:.2f} MB"


def measure(url: str, requests_count: int, timeout: float) -> list[Measurement]:
	measurements = []

	for request_number in range(1, requests_count + 1):
		print(f"Запрос {request_number}/{requests_count}...", flush=True)
		measurement = download_once(url, timeout)
		measurements.append(measurement)
		speed = measurement.downloaded_bytes / measurement.elapsed_seconds / 1_000_000
		print(
			f"  {format_bytes(measurement.downloaded_bytes)}, "
			f"{measurement.elapsed_seconds:.3f} с, {speed:.2f} MB/s"
		)

	return measurements


def build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Последовательно скачивает URL и измеряет скорость загрузки."
	)
	parser.add_argument("url", help="URL файла для скачивания")
	parser.add_argument(
		"-n",
		"--requests",
		type=int,
		default=DEFAULT_REQUESTS,
		help=f"количество запросов (по умолчанию: {DEFAULT_REQUESTS})",
	)
	parser.add_argument(
		"-t",
		"--timeout",
		type=float,
		default=DEFAULT_TIMEOUT,
		help=f"таймаут одного запроса в секундах (по умолчанию: {DEFAULT_TIMEOUT:g})",
	)
	return parser


def main() -> int:
	parser = build_parser()
	arguments = parser.parse_args()

	if arguments.requests < 1:
		parser.error("--requests должен быть больше нуля")
	if arguments.timeout <= 0:
		parser.error("--timeout должен быть больше нуля")

	try:
		measurements = measure(arguments.url, arguments.requests, arguments.timeout)
	except (HTTPError, URLError, TimeoutError, OSError) as error:
		print(f"Ошибка загрузки: {error}", file=sys.stderr)
		return 1

	total_time = sum(item.elapsed_seconds for item in measurements)
	total_bytes = sum(item.downloaded_bytes for item in measurements)
	average_time = total_time / len(measurements)
	average_speed = total_bytes / total_time / 1_000_000

	print("\nИтог:")
	print(f"  Среднее время запроса: {average_time:.3f} с")
	print(f"  Скачано всего: {format_bytes(total_bytes)}")
	print(f"  Среднее за запрос: {format_bytes(total_bytes / len(measurements))}")
	print(f"  Средняя скорость: {average_speed:.2f} MB/s")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
