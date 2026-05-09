#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           🤖  AI PERSONAL AGENT  —  Powered by Blackbox     ║
║                                                              ║
║  Your intelligent assistant that manages EVERYTHING:         ║
║  • Files & Directories    • Tasks & Calendar                 ║
║  • Web Search & Browsing  • Notes & Memory                   ║
║  • Code Execution         • System Monitoring                ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import os
import argparse
import readline  # enables arrow keys and history in input()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent_core import AIAgent


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║        🤖  AI PERSONAL AGENT  —  Powered by Blackbox AI     ║
╠══════════════════════════════════════════════════════════════╣
║  I can manage your files, tasks, calendar, notes, run code,  ║
║  search the web, monitor your system, and remember things!   ║
║                                                              ║
║  Type /help for commands  |  Type /exit to quit              ║
╚══════════════════════════════════════════════════════════════╝
"""

COLORS = {
    "reset":   "\033[0m",
    "bold":    "\033[1m",
    "cyan":    "\033[96m",
    "green":   "\033[92m",
    "yellow":  "\033[93m",
    "red":     "\033[91m",
    "blue":    "\033[94m",
    "magenta": "\033[95m",
    "dim":     "\033[2m",
}


def colorize(text: str, color: str) -> str:
    """Apply ANSI color to text."""
    if not sys.stdout.isatty():
        return text
    return f"{COLORS.get(color, '')}{text}{COLORS['reset']}"


def print_banner():
    print(colorize(BANNER, "cyan"))


def print_user_prompt():
    return colorize("You › ", "green")


def print_agent_prefix():
    return colorize("Agent › ", "cyan")


def format_response(text: str) -> str:
    """Format the agent response with basic markdown-like rendering."""
    lines = text.split("\n")
    formatted = []
    for line in lines:
        # Bold headers
        if line.startswith("## "):
            formatted.append(colorize(line[3:], "bold"))
        elif line.startswith("# "):
            formatted.append(colorize(line[2:], "bold"))
        # Bullet points
        elif line.strip().startswith("- ") or line.strip().startswith("• "):
            formatted.append(colorize("  " + line.strip(), "reset"))
        # Code blocks (backtick)
        elif line.strip().startswith("`") and line.strip().endswith("`"):
            formatted.append(colorize(line, "yellow"))
        # Emoji lines (tool results, status)
        elif any(line.startswith(e) for e in ["✅", "❌", "🔧", "📋", "📝", "📅", "🧠", "🤖", "🗑️", "🧹", "📊", "⚠️"]):
            formatted.append(colorize(line, "magenta"))
        else:
            formatted.append(line)
    return "\n".join(formatted)


def run_interactive(agent: AIAgent):
    """Run the agent in interactive chat mode."""
    print_banner()
    print(colorize(f"  Model: {agent.llm.model}  |  Memory: {agent.memory.get_summary()}", "dim"))
    print()

    # Setup readline history
    history_file = os.path.expanduser("~/.ai_agent/.history")
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass
    readline.set_history_length(500)

    while True:
        try:
            user_input = input(print_user_prompt()).strip()
        except (EOFError, KeyboardInterrupt):
            print(colorize("\n\n👋 Goodbye! Your data is saved.", "yellow"))
            break

        if not user_input:
            continue

        # Save to readline history
        try:
            readline.write_history_file(history_file)
        except Exception:
            pass

        print()

        # Get response
        try:
            response = agent.chat(user_input)
        except KeyboardInterrupt:
            print(colorize("\n⚠️  Interrupted.", "yellow"))
            continue
        except Exception as e:
            print(colorize(f"❌ Unexpected error: {e}", "red"))
            continue

        if response == "__EXIT__":
            print(colorize("👋 Goodbye! Your tasks, notes, and memories are saved.", "yellow"))
            break

        # Print formatted response
        print(print_agent_prefix())
        print(format_response(response))
        print()


def run_single_query(agent: AIAgent, query: str):
    """Run a single query and print the result (non-interactive mode)."""
    response = agent.chat(query)
    if response != "__EXIT__":
        print(response)


def main():
    parser = argparse.ArgumentParser(
        description="🤖 AI Personal Agent — manages everything via Blackbox AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python agent.py                          # Interactive mode
  python agent.py -q "What's the weather?" # Single query
  python agent.py --model gpt4             # Use GPT-4
  python agent.py --verbose                # Show tool calls
  python agent.py -q "List my tasks"       # Quick task check
        """,
    )
    parser.add_argument(
        "-q", "--query",
        type=str,
        default=None,
        help="Run a single query and exit (non-interactive mode)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="default",
        choices=["default", "gpt4", "claude", "gemini", "deepseek"],
        help="LLM model to use (default: blackboxai)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show tool calls and results",
    )
    parser.add_argument(
        "--clear-history",
        action="store_true",
        help="Clear conversation history before starting",
    )

    args = parser.parse_args()

    # Initialize agent
    try:
        agent = AIAgent(model=args.model, verbose=args.verbose)
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        sys.exit(1)

    if args.clear_history:
        agent.memory.clear()
        agent._init_system_message()
        print("🧹 History cleared.")

    if args.query:
        run_single_query(agent, args.query)
    else:
        run_interactive(agent)


if __name__ == "__main__":
    main()
