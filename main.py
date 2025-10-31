# -*- coding: utf-8 -*-
import random
from aiohttp.helpers import TimeoutHandle
import discord
import asyncio
from discord.ext import commands
import os
from typing import Optional
from discord import app_commands
from conect_mysql import insert_data, get_data, delete_data, delete_command_data

from dotenv import load_dotenv

load_dotenv()

#botの設定
intents = discord.Intents.default()
intents.message_content = True  # メッセージ内容の取得を有効化
intents.members = True  # メンバー情報の取得を有効化

bot = commands.Bot(
    command_prefix='!',  # コマンドの接頭辞
    intents=intents  # インテントの設定
)
last_help_message_id = None
last_help_command_id = None


#botの起動時に実行されるイベント
@bot.event
async def on_ready():
    print('----------------------------------')
    print(f'ログインしました: {bot.user}')
    if bot.user is not None:
        print(f'ユーザーID: {bot.user.id}')
    print(f'サーバー数: {len(bot.guilds)}')
    print('----------------------------------')
    # ステータスの設定
    await bot.change_presence(status=discord.Status.online,
                              activity=discord.CustomActivity(name="!help"))
    # Webページの監視を開始
    # monitoring_task = asyncio.create_task(monitor_website())
    # print("ウェブサイト監視タスクをバックグラウンドで開始しました。")
    # get_latest_youtube_updates()


#メッセージ受信時に実行されるイベント
@bot.event
async def on_message(message):
    # bot自身のメッセージは無視
    if message.author == bot.user:
        return

    #「こんにちは」とメッセージがあった場合の応答
    if "こんにちは" in message.content:
        await message.channel.send(f"こんにちは、{message.author}さん！")
        await message.author.send("こんにちは！")
        print(f"{message.author}さんが'こんにちは'と言いました。")

    # 他のコマンドも処理する
    await bot.process_commands(message)


@bot.event
async def on_member_join(member):
    """新しいメンバーが参加したときに実行されるイベント"""
    channel = member.guild.system_channel  # システムチャンネルを取得
    if channel:
        await channel.send(f"ようこそ、{member.mention}さん！チンチロをしましょう!")
        print(f"{member}さんがサーバーに参加しました。")
    else:
        print(f"{member}さんがサーバーに参加しましたが、システムチャンネルが見つかりませんでした。")


# helpコマンドを上書き
bot.remove_command('help')


@bot.command(name='help')
async def custom_help(ctx):
    """コマンド一覧を表示します。"""

    # データベースからデータを取得
    rows = get_data()

    if rows:
        last_help_message_id = rows[-1].get("message_id")
        last_help_command_id = rows[-1].get("command_id")
    else:
        last_help_message_id = None
        last_help_command_id = None


    # 以前のヘルプメッセージがあれば削除
    if last_help_message_id:
        try:
            # Discord上のメッセージ削除
            old_message = await ctx.channel.fetch_message(last_help_message_id)
            await old_message.delete()
            #print(f"以前のヘルプメッセージをDiscord上から削除: {last_help_message_id}")
        except discord.NotFound:
            #print("以前のヘルプメッセージは既に削除済み")
            pass
        except Exception as e:
            print(f"Discordメッセージ削除エラー: {e}")
        # DB上のデータ削除
        await asyncio.to_thread(delete_data, last_help_message_id)
        #print(f"以前のヘルプメッセージをDBから削除: {last_help_message_id}")

    # 以前のコマンドメッセージがあれば削除
    if last_help_command_id:
        try:
            old_command_message = await ctx.channel.fetch_message(last_help_command_id)
            await old_command_message.delete()
            #print(f"以前のコマンドメッセージをDiscord上から削除: {last_help_command_id}")
        except discord.NotFound:
            #print("以前のコマンドメッセージは既に削除済み")
            pass
        except Exception as e:
            print(f"Discordコマンドメッセージ削除エラー: {e}")
        # DB上のデータ削除
        await asyncio.to_thread(delete_command_data, last_help_command_id)
        #print(f"以前のコマンドメッセージをDBから削除: {last_help_command_id}")

    # 新しいヘルプメニューを作成
    embed = discord.Embed(title="📘 コマンド一覧", description="コマンドは ! を付けて実行してください。", color=discord.Color.blue())
    for command in bot.commands:
        usage = command.name
        if command.name == "dice":
            usage += " [面数]"
        if command.name == "userinfo":
            usage += " [ユーザー名]"
        if command.name == "janken":
            usage += " [ぐー,ちょき,ぱー]"
        embed.add_field(
            name=usage,
            value=command.help or "説明なし",
            inline=False
        )
    sent = await ctx.send(embed=embed)

    # メッセージIDを保存
    last_help_message_id = sent.id
    last_help_command_id = ctx.message.id

    # データベースに保存
    await asyncio.to_thread(insert_data, last_help_message_id, last_help_command_id)

    #print(f"ヘルプメッセージID: {last_help_message_id}")
    print(f"{ctx.author} さんがヘルプを確認しました。")


#pingコマンド
@bot.command(name='ping')
async def ping(ctx):
    """botの応答速度を測定します。"""
    latency = round(bot.latency * 1000)  # ミリ秒に変換
    await ctx.send(f'Pong! 応答速度：{latency}ms')
    print(f"{ctx.author}さんが'ping'と言いました。")


#ユーザー情報コマンド
@bot.command(name='userinfo')
async def userinfo(ctx, member: Optional[discord.Member] = None):
    """指定したユーザー(未入力の場合はあなた)の情報を表示します。"""
    member = member or ctx.author  # メンバーが指定されていない場合はコマンド実行者を使用

    embed = discord.Embed(title=f"{member.name}の情報", color= discord.Color.green())

    # アバターがある場合のみ設定
    if member.avatar:
        embed.set_thumbnail(url=member.avatar.url)

    embed.add_field(name="名前", value=member.name)
    embed.add_field(name="ID", value=member.id)

    # サーバー参加日（Noneチェック）
    if member.joined_at:
        embed.add_field(name="サーバー参加日",
                        value=member.joined_at.strftime("%Y/%m/%d"),inline=False)

    # アカウント作成日
    embed.add_field(name="アカウント作成日",
                    value=member.created_at.strftime("%Y/%m/%d"),inline=True)

    await ctx.send(embed=embed)
    print(f"{ctx.author}さんが'{member.name}の情報'を確認しました。")


#サイコロコマンド
@bot.command(name='dice')
async def dice(ctx, sides: int = 6):
    """サイコロを振ります。デフォルト(面数未入力)は6面です。"""
    import random
    result = random.randint(1, sides)
    await ctx.send(f'🎲 {ctx.author.mention} さんが {sides} 面サイコロを振りました。結果は {result} です！')
    print(f"{ctx.author}さんが'{sides}面サイコロ'を振りました。結果は{result}です。")


#チンチロコマンド
@bot.command(name='dice3')
async def dice3(ctx):
    """チンチロをします。"""
    result1 = random.randint(1, 6)
    result2 = random.randint(1, 6)
    result3 = random.randint(1, 6)
    result = None
    
    if result1 == result2 == result3:
        result = "ぞろ目"
    elif sorted([result1, result2, result3]) == [4, 5, 6]:
        result = "シゴロ"
    elif sorted([result1, result2, result3]) == [1, 2, 3]:
        result = "ヒフミ"
    elif result1 == result2:
        result = f"出目は{result3}"
    elif result2 == result3:
        result = f"出目は{result1}"
    elif result3 == result1:
        result = f"出目は{result2}"
    else:
        result = "目無し"
    await ctx.send(f'🎲 {ctx.author.mention} さんが3つサイコロを振りました。結果は {result1} , {result2} , {result3} ,{result}です！')
    print(f"{ctx.author}さんが'3つサイコロ'を振りました。結果は{result1} , {result2} , {result3},{result}です。")

choices = ["ぐー", "ちょき", "ぱー"]
#じゃんけんコマンド
@bot.command(name='janken')
async def janken(ctx, hand: str=random.choice(choices)):
    """じゃんけんをします。ぐー, ちょき, ぱーのいずれかを指定してください。未入力の場合はランダムに決めます。"""
    choices = ["ぐー", "ちょき", "ぱー"]
    if hand is None:
        hand = random.choice(choices)
    bot_choice = random.choice(choices)
    await ctx.send(f'じゃんけん！ {ctx.author.mention} さんは {hand} を出しました。botは')
    await asyncio.sleep(1)
    await ctx.send(f'{bot_choice} を出しました。')
    if hand == bot_choice:
        await ctx.send("あいこです！")
    elif (hand == "ぐー" and bot_choice == "ちょき") or (hand == "ちょき" and bot_choice == "ぱー") or (hand == "ぱー" and bot_choice == "ぐー"):
        await ctx.send(f"{ctx.author.mention} さんの勝ちです！")
    else:
        await ctx.send("botの勝ちです！")
    
    

# # YouTubeチャンネルの最新動画を取得するコマンド
# @bot.command(name='youtube')
# async def youtube(ctx):
#     """最新YouTube動画情報を送信"""
#     embed = get_latest_youtube_updates_embed()
#     if embed is None:
#         await ctx.send("情報を取得できませんでした。")
#     else:
#         await ctx.send(embed=embed)

# # X（旧Twitter）の最新投稿を取得するコマンド
# @bot.command(name='x')
# async def x_command(ctx):
#     """最新X（旧Twitter）の投稿をEmbedで送信"""
#     embed = get_latest_x_updates_embed(USERNAME)
#     if embed is None:
#         await ctx.send("投稿情報を取得できませんでした。")
#     else:
#         await ctx.send(embed=embed)

#bot実行
my_secret = os.getenv('TOKEN')
try:
    bot.run(my_secret)
except discord.errors.LoginFailure:
    print("ログイン失敗: TOKENを確認してください")
    os.system("kill")
except Exception as e:
    print(f"予期せぬエラーが発生しました: {e}")