"""Win365: independent everyday productivity Telegram bot."""
import ast
import logging
import os
from pathlib import Path

from telegram import BotCommand, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

BOT_NAME = "Win365"
BOT_ABOUT = "Count words and characters, calculate numbers, and get simple tool instructions with Win365."
BOT_DESCRIPTION = (
    "Welcome to Win365, an independent everyday utility bot.\n\n"
    "Text Counter: Count words, characters and lines.\n"
    "Quick Calculator: Solve basic arithmetic expressions.\n"
    "Help & Information: Learn how to use each feature.\n\n"
    "Choose one of the three menu buttons to start."
)

TEXT_BUTTON = "Text Counter"
CALC_BUTTON = "Quick Calculator"
HELP_BUTTON = "Help & Information"
KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton(TEXT_BUTTON)], [KeyboardButton(CALC_BUTTON)], [KeyboardButton(HELP_BUTTON)]],
    resize_keyboard=True,
    is_persistent=True,
)

WELCOME = (
    "Welcome to Win365!\n\n"
    "Your simple assistant for everyday tasks.\n\n"
    "Choose Text Counter, Quick Calculator, or Help & Information below to get started."
)
HELP_TEXT = (
    "Win365 — Help & Information\n\n"
    "Text Counter: Count words, characters, and lines in your text.\n"
    "Quick Calculator: Enter an expression such as (12 + 8) / 4.\n"
    "Help & Information: View the available functions.\n\n"
    "Commands: /start, /count, /calc, /help, /cancel.\n"
    "Use /cancel to leave a tool.\n\n"
    "Win365 is an independent productivity utility bot."
)


def evaluate_expression(expression: str) -> str:
    """Safely evaluate a limited arithmetic expression without eval()."""
    if len(expression) > 100:
        raise ValueError("Expression is too long (maximum 100 characters).")
    expression = expression.strip().replace("^", "**").replace("×", "*").replace("÷", "/")
    if not expression:
        raise ValueError("Enter a calculation, for example: (12 + 8) / 4.")
    try:
        root = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError("Invalid expression. Use numbers, +, -, *, /, ^ or parentheses.") from exc

    nodes = 0

    def walk(node: ast.AST, depth: int = 0) -> float:
        nonlocal nodes
        nodes += 1
        if nodes > 50 or depth > 16:
            raise ValueError("Expression is too complex.")
        if isinstance(node, ast.Expression):
            return walk(node.body, depth + 1)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            number = float(node.value)
            if abs(number) > 1e12:
                raise ValueError("Numbers must be within 1 trillion.")
            return number
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            number = walk(node.operand, depth + 1)
            return number if isinstance(node.op, ast.UAdd) else -number
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
            left, right = walk(node.left, depth + 1), walk(node.right, depth + 1)
            if isinstance(node.op, ast.Add):
                result = left + right
            elif isinstance(node.op, ast.Sub):
                result = left - right
            elif isinstance(node.op, ast.Mult):
                result = left * right
            elif isinstance(node.op, ast.Div):
                if right == 0:
                    raise ValueError("Cannot divide by zero.")
                result = left / right
            else:
                if abs(right) > 12 or abs(left) > 1e6:
                    raise ValueError("Exponent is too large.")
                result = left ** right
            if isinstance(result, complex) or not (-1e15 <= result <= 1e15):
                raise ValueError("Result is outside the supported range.")
            return float(result)
        raise ValueError("Only basic arithmetic is supported. No variables or functions.")

    try:
        answer = walk(root)
    except (OverflowError, ZeroDivisionError) as exc:
        raise ValueError("This calculation is outside the supported range.") from exc
    return f"{answer:,.10f}".rstrip("0").rstrip(".") if not answer.is_integer() else f"{answer:,.0f}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = None
    await update.effective_message.reply_text(WELCOME, reply_markup=KEYBOARD)


async def text_counter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = "text"
    await update.effective_message.reply_text(
        "Text Counter\n\nSend text to count words, characters, and lines.\nUse /cancel to exit.",
        reply_markup=KEYBOARD,
    )



async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = "calculator"
    await update.effective_message.reply_text(
        "Quick Calculator\n\nType an expression such as (12 + 8) / 4.\n"
        "Supported: +, -, *, /, ^, parentheses.\nSend /cancel to exit.",
        reply_markup=KEYBOARD,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = None
    await update.effective_message.reply_text(HELP_TEXT, reply_markup=KEYBOARD)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["mode"] = None
    await update.effective_message.reply_text("Tool closed. Choose a button below.", reply_markup=KEYBOARD)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    content = (message.text or "").strip()
    if content == TEXT_BUTTON:
        await text_counter(update, context)
    elif content == CALC_BUTTON:
        await calc(update, context)
    elif content == HELP_BUTTON:
        await help_command(update, context)
    elif context.user_data.get("mode") == "text":
        if len(content) > 4000:
            await message.reply_text("Please send up to 4,000 characters.", reply_markup=KEYBOARD)
            return
        await message.reply_text(
            f"Words: {len(content.split())}\n"
            f"Characters: {len(content)}\n"
            f"Lines: {len(content.splitlines())}\n\n"
            "Send more text or /cancel.",
            reply_markup=KEYBOARD,
        )
    elif context.user_data.get("mode") == "calculator":
        try:
            result = evaluate_expression(content)
            await message.reply_text(f"Result: {result}\n\nSend another expression or /cancel.", reply_markup=KEYBOARD)
        except ValueError as exc:
            await message.reply_text(f"Could not calculate: {exc}\nTry again or /cancel.", reply_markup=KEYBOARD)
    else:
        await message.reply_text("Please select one of the three buttons below or use /help.", reply_markup=KEYBOARD)

async def post_init(application: Application) -> None:
    bot = application.bot
    await bot.set_my_name(name=BOT_NAME)
    await bot.set_my_short_description(short_description=BOT_ABOUT)
    await bot.set_my_description(description=BOT_DESCRIPTION)
    await bot.set_my_commands([
        BotCommand("start", "Open the Win365 menu"),
        BotCommand("count", "Count words, characters, and lines"),
        BotCommand("calc", "Use the quick calculator"),
        BotCommand("help", "See features and instructions"),
        BotCommand("cancel", "Exit calculator mode"),
    ])
    logger.info("Win365 profile and command menu updated")


def main() -> None:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is required.")
    application = Application.builder().token(token).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("count", text_counter))
    application.add_handler(CommandHandler("calc", calc))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_text))
    logger.info("Win365 bot starting")
    application.run_polling(drop_pending_updates=False)


if __name__ == "__main__":
    main()
