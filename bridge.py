import argparse
import json
from miro_client import get_board_items, create_sticky_note


def handle_read(args):
    items = get_board_items()
    output = {"items": items}

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Read {len(items)} items from board. Saved to {args.output}")


def handle_write(args):
    with open(args.plan, "r") as f:
        plan = json.load(f)

    spacing = 300
    base_x = 0
    y = 0

    for i, step in enumerate(plan):
        x = step.get("x", base_x + i * spacing)
        step_y = step.get("y", y)
        title = step.get("title") or step.get("description") or f"Step {i + 1}"

        create_sticky_note(title, x, step_y)

    print(f"Wrote {len(plan)} sticky notes to board.")


def main():
    parser = argparse.ArgumentParser(description="Canvas-to-Code Bridge CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    read_parser = subparsers.add_parser("read", help="Read items from Miro board")
    read_parser.add_argument(
        "--output",
        default="board_content.json",
        help="Output file path (default: board_content.json)"
    )

    write_parser = subparsers.add_parser("write", help="Write plan to Miro board")
    write_parser.add_argument(
        "--plan",
        default="plans/current_plan.json",
        help="Plan JSON file path (default: plans/current_plan.json)"
    )

    args = parser.parse_args()

    if args.command == "read":
        handle_read(args)
    elif args.command == "write":
        handle_write(args)


if __name__ == "__main__":
    main()
