"""Benchmark the tailwhip sorting algorithm."""

import statistics
import time

from tailwhip.sorting import sort_classes
from tailwhip.tests.test_shuffled_sorting import CLASS_GROUPS, shuffle


def run_benchmark(run_count: int) -> None:
    """Run the benchmark `run_count` times and print the results."""
    timings = []
    for i in range(run_count):
        start_time = time.perf_counter()

        for classes in CLASS_GROUPS:
            shuffled_classes = shuffle(classes)
            sort_classes(shuffled_classes)

        end_time = time.perf_counter()
        timings.append(end_time - start_time)
        print(f"Run {i + 1}/{run_count} completed in {timings[-1]:.4f} seconds.")

    print("\n--- Benchmark Results ---")
    print(f"Total runs: {run_count}")
    print(f"Median time: {statistics.median(timings):.4f} seconds")
    print(f"Average time: {statistics.mean(timings):.4f} seconds")
    print(f"Standard deviation: {statistics.stdev(timings):.4f} seconds")
    print(f"Min time: {min(timings):.4f} seconds")
    print(f"Max time: {max(timings):.4f} seconds")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Benchmark the tailwhip sorting algorithm."
    )
    parser.add_argument(
        "-n",
        "--runs",
        type=int,
        default=10,
        help="The number of times to run the benchmark.",
    )
    args = parser.parse_args()

    run_benchmark(args.runs)
