#!/usr/bin/python3
import discord
import json
import asyncio
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure, MissingPermissions

MAX_VOICE_CHANNELS = 100
CDUBHEX = 0xFFFF00


def findIndexedChannel(guildID):
    with open("voiceChannels.json", "r") as f:
        document = json.load(f)
    for i in range(len(document["servers"])):
        if document["servers"][i]["id"] == int(guildID):
            return i


def get_prefix(client, message):
    with open("prefixes.json", "r") as f:
        prefixes = json.load(f)
    return prefixes[str(message.guild.id)]


def notAlreadyChannel(channelLocation, VOICECHANNEL):
    for i in channelLocation:
        if i["id"] == VOICECHANNEL.id:
            return False
    return True


bot = commands.Bot(command_prefix=get_prefix)


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.CustomActivity(
            name="Designed By: TheSmallNut", type=discord.ActivityType.custom
        )
    )
    print("Bot is ready.")


async def createVoiceChannelFromMainChannel(mainChannel):
    voiceChannelNumber = len(mainChannel["insideChannels"]) + 2
    name = mainChannel["name"].rsplit(" ", 1)
    channel = bot.get_channel(mainChannel["id"])
    return await channel.guild.create_voice_channel(
        name=name[0] + " " + str(voiceChannelNumber),
        category=channel.category,
        user_limit=channel.user_limit,
        bitrate=channel.bitrate,
        position=channel.position + 1,
    )


def getInsideChannel(document, guild, channelID):
    channels = document["servers"][findIndexedChannel(guild.id)]["channels"]
    for channel in channels:
        for indexedChannel in channel["insideChannels" ]:
            if indexedChannel["id"]== channelID:
                return channel

def logMainChannel(mainChannel, channel):
    mainChannel["insideChannels"].append({})
    lastChannel = mainChannel["insideChannels"][-1]
    lastChannel["id"] = channel.id
    lastChannel["mainID"] = mainChannel["id"]
    return mainChannel


async def joinedChannel(after, guild):
    with open("voiceChannels.json", "r") as f:
        document = json.load(f)
    channelID = after.channel.id
    for mainChannel in document["servers"][findIndexedChannel(guild.id)]["channels"]:
        if mainChannel["id"] == channelID:
            channel = await createVoiceChannelFromMainChannel(mainChannel)
            mainChannel = logMainChannel(mainChannel, channel)
            return document
    mainChannel = getInsideChannel(document, guild, channelID)
    channel = await createVoiceChannelFromMainChannel(mainChannel)
    mainChannel = logMainChannel(mainChannel, channel)
    return document
    
async def deleteVoiceChannels(before):
    pass


@bot.event
async def on_voice_state_update(member, before, after):
    guild = member.guild
    if before.channel != after.channel:
        if after.channel == None:
            await deleteVoiceChannels(before)
        else:
            document = await joinedChannel(after, guild)
            with open("voiceChannels.json", "w") as f:
                json.dump(document, f, indent=4)


@bot.event
async def on_guild_join(guild):
    with open("prefixes.json", "r") as f:
        prefixes = json.load(f)
    prefixes[str(guild.id)] = "."

    with open("prefixes.json", "w") as f:
        json.dump(prefixes, f, indent=4)

    with open("voiceChannels.json", "r") as f:
        voiceDocument = json.load(f)
    voiceDocument["servers"].append({})
    voiceDocument["servers"][len(voiceDocument["servers"]) - 1]["id"] = guild.id
    voiceDocument["servers"][len(voiceDocument["servers"]) - 1]["name"] = guild.name
    voiceDocument["servers"][len(voiceDocument["servers"]) - 1]["channels"] = []
    with open("voiceChannels.json", "w") as f:
        json.dump(voiceDocument, f, indent=4)


@bot.event
async def on_guild_remove(guild):
    with open("prefixes.json", "r") as f:
        prefixes = json.load(f)
    prefixes.pop(str(guild.id))

    with open("prefixes.json", "w") as f:
        json.dump(prefixes, f, indent=4)

    with open("voiceChannels.json", "r") as f:
        voiceDocument = json.load(f)

    del voiceDocument["servers"][findIndexedChannel(guild.id)]

    with open("voiceChannels.json", "w") as f:
        json.dump(voiceDocument, f, indent=4)


@bot.event
async def on_message(ctx):
    print(ctx.content)
    await bot.process_commands(ctx)


@bot.command()
async def setMainVoiceChannel(ctx, voiceChannelID):
    guild = ctx.guild
    VOICECHANNEL = discord.utils.get(guild.voice_channels, id=int(voiceChannelID))
    with open("voiceChannels.json", "r") as f:
        voiceDocument = json.load(f)

    channelLocation = voiceDocument["servers"][findIndexedChannel(guild.id)]["channels"]
    if notAlreadyChannel(channelLocation, VOICECHANNEL):

        channelLocation.append({})
        location = channelLocation[len(channelLocation) - 1]
        location["name"] = VOICECHANNEL.name
        location["category"] = VOICECHANNEL.category_id
        location["position"] = VOICECHANNEL.position
        location["user_limit"] = VOICECHANNEL.user_limit
        location["bitrate"] = VOICECHANNEL.bitrate
        location["id"] = VOICECHANNEL.id
        location["insideChannels"] = []
        with open("voiceChannels.json", "w") as outfile:
            json.dump(voiceDocument, outfile, indent=4)
        embedVar = discord.Embed(
            title=f'Voice channel "{VOICECHANNEL.name}" set as a main voice channel',
            color=CDUBHEX,
        )
        await ctx.send(embed=embedVar)
    else:
        embedVar = discord.Embed(
            title=f'Voice channel "{VOICECHANNEL.name}" is already a main voice channel',
            color=0xAE0700,
        )
        await ctx.send(embed=embedVar)


@bot.command(name="changeprefix", aliases=["cp", "change prefix"])
@has_permissions(manage_messages=True)
async def changeprefix(ctx, prefix):
    with open("prefixes.json", "r") as f:
        prefixes = json.load(f)
    prefixes[str(ctx.guild.id)] = prefix

    with open("prefixes.json", "w") as f:
        json.dump(prefixes, f, indent=4)
    embedVar = discord.Embed(
        title=f"Done! Prefix is now: {prefix}",
        color=CDUBHEX,
    )
    await ctx.send(embed=embedVar)


@bot.command()
async def ping(ctx):
    embedVar = discord.Embed(
        title=f"Pong! {round(bot.latency * 1000)}ms",
        color=CDUBHEX,
    )
    await ctx.send(embed=embedVar)


@changeprefix.error
async def change_prefix_error(self, ctx, error):
    if isinstance(error, MissingPermissions):
        await ctx.send(":redTick: You don't have permission to kick members.")

key = open("key.gitignore", 'r')
key = key.read()

bot.run(key)
