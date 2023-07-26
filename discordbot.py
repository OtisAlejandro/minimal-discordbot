import discord
from discord.ext.commands import Bot
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from langchain.llms import KoboldApiLLM, TextGen
import json
import os
import asyncio

# Add this at the top of your script
from collections import defaultdict

# Initialize a dictionary for channel memories
channel_memories = defaultdict(ConversationSummaryBufferMemory)

# Initialize bot
intents = discord.Intents.all()
bot = Bot(command_prefix="/", intents=intents, help_command=None)

# Load configuration from config.json
with open("config.json", "r") as file:
    config = json.load(file)

bot.token = config["required"]["TOKEN"]
bot.endpoint = config["required"]["ENDPOINT"]
bot.channels = [int(x) for x in config["required"]["CHANNELS"].split(",")]
bot.name = config["required"]["NAME"]
bot.prompt = config["required"]["PROMPT"].replace("{{char}}", bot.name)

# Extras
if config["extras"]["MENTION"].lower() == "t":
    bot.mention = True
bot.stop_sequences = defaultdict(lambda: config["extras"]["STOP_SEQUENCES"].split(","))

# Initialize the langchain components
TEMPLATE = f"""### Instruction:
{bot.prompt.replace('{{char}}', bot.name)}
{{history}}
{{input}}
### Response:
{bot.name}:"""

PROMPT = PromptTemplate(input_variables=["history", "input"], template=TEMPLATE)


async def endpoint_test(endpoint):
    try:
        llm = KoboldApiLLM(endpoint=endpoint)
        llm("Question: What is the sum of 2 and 2?\nAnswer:")
        return llm
    except:
        print("Kobold API failed, trying TextGen")
        try:
            llm = TextGen(model_url=endpoint)
            llm("Question: What is the sum of 2 and 2?\nAnswer:")
            return llm
        except:
            pass


async def get_memory_for_channel(channel_id):
    # If the memory for this channel doesn't exist, create it
    if channel_id not in channel_memories:
        channel_memories[channel_id] = ConversationSummaryBufferMemory(
            llm=bot.llm, max_token_limit=10
        )
    return channel_memories[channel_id]


async def generate_response(name, channel_id, message_content):
    memory = await get_memory_for_channel(str(channel_id))
    stop_sequence = await get_stop_sequence_for_channel(channel_id, name)
    formatted_message = f"{name}: {message_content}"
    conversation = ConversationChain(
        prompt=PROMPT,
        llm=bot.llm,
        verbose=True,
        memory=memory,
    )

    input_dict = {"input": formatted_message, "stop": stop_sequence}
    response = conversation(input_dict)

    return response["response"]


async def add_history(name, channel_id, message_content):
    memory = await get_memory_for_channel(str(channel_id))
    formatted_message = f"{name}: {message_content}"
    memory.add_input_only(formatted_message)
    return None


async def get_stop_sequence_for_channel(channel_id, name):
    name_token = f"\n{name}:"
    if name_token not in bot.stop_sequences[channel_id]:
        bot.stop_sequences[channel_id].append(name_token)
    return bot.stop_sequences[channel_id]


async def get_messages_by_channel(channel_id):
    channel = bot.get_channel(int(channel_id))
    messages = []

    async for message in channel.history(limit=None):
        # Skip messages that start with '.' or '/'
        if message.content.startswith(".") or message.content.startswith("/"):
            continue

        messages.append(
            (
                message.author.display_name,
                message.channel.id,
                message.clean_content.replace("\n", " "),
            )
        )

        # Break the loop once we have at least 5 non-skipped messages
        if len(messages) >= 10:
            break

    # Return the first 5 non-skipped messages
    return messages[:10]


@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    bot.llm = await endpoint_test(bot.endpoint)

    # Initialize memory and conversation chain after bot.llm is set
    memory = ConversationSummaryBufferMemory(llm=bot.llm, max_token_limit=800)
    bot.conversation = ConversationChain(
        prompt=PROMPT,
        llm=bot.llm,
        verbose=True,
        memory=memory,
    )


@bot.event
async def on_message(message):
    # Don't process messages sent by the bot
    if message.author == bot.user:
        return

    # Only process messages in specified channels
    if message.channel.id not in bot.channels:
        return

    async with message.channel.typing():
        if bot.mention and bot.name.lower() in message.clean_content.lower():
            response = await generate_response(
                bot.name, message.channel.id, message.clean_content
            )
            await message.channel.send(response)


async def load_cogs() -> None:
    for file in os.listdir(f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
        if file.endswith(".py"):
            extension = file[:-3]
            try:
                await bot.load_extension(f"cogs.{extension}")
            except Exception as e:
                # log the error and continue with the next file
                error_info = (
                    f"Failed to load extension {extension}. {type(e).__name__}: {e}"
                )
                print(error_info)


asyncio.run(load_cogs())
bot.run(bot.token)
