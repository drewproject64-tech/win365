"""Win365: independent everyday productivity Telegram bot."""
import ast
import logging
import os
import random
from decimal import Decimal
from pathlib import Path

from telegram import BotCommand, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

BOT_NAME = "Win365"
BOT_ABOUT = "Win365 provides simple daily tools, helpful tips, and practical utilities for everyday tasks."
BOT_DESCRIPTION = (
    "Welcome to Win365, your everyday digital assistant.\n\n"
    "Explore quick calculations, discover useful productivity tips, and access "
    "simple tools to make daily tasks easier.\n\n"
    "Choose a function from the menu to get started."
)

TIPS_BUTTON = "Daily Tips"
CALC_BUTTON = "Quick Calculator"
HELP_BUTTON = "Help & Information"
KEYBOARD = ReplyKeyboardMarkup(
    [[KeyboardButton(TIPS_BUTTON)], [KeyboardButton(CALC_BUTTON)], [KeyboardButton(HELP_BUTTON)]],
    resize_keyboard=True,
    is_persistent=True,
)

TIPS = [
    "Write down your three most important tasks before you begin your day.",
    "Break a large task into small steps and complete the first step today.",
    "Set a short timer to focus on one task without interruptions.",
    "Review your calendar at the start of the day so you can plan realistically.",
    "Keep frequently used files in clearly named folders for quicker access.",
    "Take a brief screen break to refresh your focus between tasks.",
    "Set a realistic deadline for a task rather than leaving it open-ended.",
    "Finish one important task before starting several new ones.",
    "Save useful notes in one place so you can find them later.",
    "At the end of the day, note one thing you completed and one priority for tomorrow.",
]

WELCOME = (
    "Welcome to Win365!\n\n"
    "Your simple assistant for everyday tasks.\n\n"
    "Choose Daily Tips, Quick Calculator, or Help & Information below to get started."
)
HELP_TEXT = (
    "Win365 — Help & Information\n\n"
    "Daily Tips: Get a practical productivity idea.\n"
    "Quick Calculator: Enter an expression such as (12 + 8) / 4.\n"
    "Help & Information: View the available functions.\n\n"
    "Commands: /start, /tips, /calc, /help, /cancel.\n"
    "Use /cancel to leave calculator mode.\n\n"
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
    context.user_data["calculator_mode"] = False
    await update.effective_message.reply_text(WELCOME, reply_markup=KEYBOARD)


async def tips(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("Today's productivity tip:\n\n" + random.choice(TIPS), reply_markup=KEYBOARD)


async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["calculator_mode"] = True
    await update.effective_message.reply_text(
        "Quick Calculator\n\nType an expression such as (12 + 8) / 4.\n"
        "Supported: +, -, *, /, ^, parentheses.\nSend /cancel to exit.",
        reply_markup=KEYBOARD,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["calculator_mode"] = False
    await update.effective_message.reply_text(HELP_TEXT, reply_markup=KEYBOARD)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["calculator_mode"] = False
    await update.effective_message.reply_text("Calculator closed. Choose a button below.", reply_markup=KEYBOARD)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    content = (message.text or "").strip()
    if content == TIPS_BUTTON:
        await tips(update, context)
    elif content == CALC_BUTTON:
        await calc(update, context)
    elif content == HELP_BUTTON:
        await help_command(update, context)
    elif context.user_data.get("calculator_mode"):
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
        BotCommand("tips", "Get a daily productivity tip"),
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
    application.add_handler(CommandHandler("tips", tips))
    application.add_handler(CommandHandler("calc", calc))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, handle_text))
    logger.info("Win365 bot starting")
    application.run_polling(drop_pending_updates=False)


if __name__ == "__main__":
    main()
