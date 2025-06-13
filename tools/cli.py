#!/usr/bin/env python3
"""
CLI-утилита для управления API-ключами и тарифами в LLM Gateway

Использование:
    python tools/cli.py create-key --limit 100000 [--name "Custom Plan"]
    python tools/cli.py revoke-key --key sk-abc123...
    python tools/cli.py list-keys
    python tools/cli.py set-limit --key sk-abc123... --limit 200000
    python tools/cli.py stats
    python tools/cli.py backup [--path backup.json]
    python tools/cli.py restore --path backup.json
"""

import sys
import argparse
from pathlib import Path

# Импортируем локальные утилиты для работы с ключами
from key_utils import (
    load_keys, save_keys, generate_api_key, validate_key_format,
    add_key, remove_key, update_key_limit, get_key_info, 
    list_all_keys, get_keys_stats, backup_keys, restore_keys
)


def create_key_command(args):
    """Создание нового API-ключа"""
    try:
        # Генерируем новый ключ
        new_key = generate_api_key()
        
        # Добавляем ключ с указанными параметрами
        success = add_key(
            key=new_key,
            max_tokens=args.limit,
            name=args.name or "CLI Generated",
            description=args.description or f"Ключ создан через CLI с лимитом {args.limit} токенов"
        )
        
        if success:
            print(f"✅ API-ключ успешно создан:")
            print(f"   Ключ: {new_key}")
            print(f"   Лимит токенов: {args.limit:,}")
            print(f"   Название: {args.name or 'CLI Generated'}")
            
            # Обновляем .env файл если нужно
            if args.add_to_env:
                update_env_file(new_key)
        else:
            print("❌ Ошибка при создании API-ключа")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


def revoke_key_command(args):
    """Удаление API-ключа"""
    try:
        # Проверяем формат ключа
        if not validate_key_format(args.key):
            print(f"❌ Неверный формат ключа: {args.key}")
            sys.exit(1)
        
        # Получаем информацию о ключе перед удалением
        key_info = get_key_info(args.key)
        if not key_info:
            print(f"❌ Ключ не найден: {args.key}")
            sys.exit(1)
        
        # Подтверждение удаления
        if not args.force:
            masked_key = args.key[:12] + "..." + args.key[-4:]
            print(f"⚠️  Вы действительно хотите удалить ключ {masked_key}?")
            print(f"   Лимит: {key_info.get('max_tokens', 0):,} токенов")
            print(f"   Название: {key_info.get('name', 'N/A')}")
            
            confirm = input("Введите 'yes' для подтверждения: ").strip().lower()
            if confirm != 'yes':
                print("❌ Удаление отменено")
                return
        
        # Удаляем ключ
        success = remove_key(args.key)
        
        if success:
            masked_key = args.key[:12] + "..." + args.key[-4:]
            print(f"✅ API-ключ {masked_key} успешно удален")
        else:
            print("❌ Ошибка при удалении API-ключа")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


def list_keys_command(args):
    """Вывод списка всех API-ключей"""
    try:
        keys = list_all_keys()
        
        if not keys:
            print("📝 API-ключи не найдены")
            return
        
        print(f"📋 Список API-ключей ({len(keys)} шт.):")
        print("=" * 80)
        
        # Сортируем ключи по лимиту токенов (по убыванию)
        sorted_keys = sorted(
            keys.items(), 
            key=lambda x: x[1].get('max_tokens', 0), 
            reverse=True
        )
        
        for key, info in sorted_keys:
            masked_key = key[:12] + "..." + key[-4:] if len(key) > 16 else key
            max_tokens = info.get('max_tokens', 0)
            name = info.get('name', 'N/A')
            description = info.get('description', 'N/A')
            
            print(f"🔑 {masked_key}")
            print(f"   📊 Лимит: {max_tokens:,} токенов")
            print(f"   🏷️  Название: {name}")
            if args.verbose:
                print(f"   📝 Описание: {description}")
            print()
        
        # Показываем статистику
        if args.stats:
            stats = get_keys_stats()
            print("📈 Статистика:")
            print(f"   Всего ключей: {stats['total_keys']}")
            print(f"   Общий лимит: {stats['total_tokens']:,} токенов")
            print(f"   Средний лимит: {stats['avg_tokens']:,} токенов")
            print(f"   Мин. лимит: {stats['min_tokens']:,} токенов")
            print(f"   Макс. лимит: {stats['max_tokens']:,} токенов")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


def set_limit_command(args):
    """Обновление лимита токенов для ключа"""
    try:
        # Проверяем формат ключа
        if not validate_key_format(args.key):
            print(f"❌ Неверный формат ключа: {args.key}")
            sys.exit(1)
        
        # Получаем текущую информацию о ключе
        key_info = get_key_info(args.key)
        if not key_info:
            print(f"❌ Ключ не найден: {args.key}")
            sys.exit(1)
        
        old_limit = key_info.get('max_tokens', 0)
        
        # Обновляем лимит
        success = update_key_limit(args.key, args.limit)
        
        if success:
            masked_key = args.key[:12] + "..." + args.key[-4:]
            print(f"✅ Лимит токенов обновлен для ключа {masked_key}")
            print(f"   Старый лимит: {old_limit:,} токенов")
            print(f"   Новый лимит: {args.limit:,} токенов")
            
            # Показываем изменение в процентах
            if old_limit > 0:
                change_percent = ((args.limit - old_limit) / old_limit) * 100
                change_sign = "+" if change_percent > 0 else ""
                print(f"   Изменение: {change_sign}{change_percent:.1f}%")
        else:
            print("❌ Ошибка при обновлении лимита")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


def stats_command(args):
    """Вывод статистики по API-ключам"""
    try:
        stats = get_keys_stats()
        keys = list_all_keys()
        
        print("📊 Статистика API-ключей:")
        print("=" * 40)
        print(f"📝 Всего ключей: {stats['total_keys']}")
        print(f"🎯 Общий лимит: {stats['total_tokens']:,} токенов")
        
        if stats['total_keys'] > 0:
            print(f"📊 Средний лимит: {stats['avg_tokens']:,} токенов")
            print(f"📉 Минимальный лимит: {stats['min_tokens']:,} токенов")
            print(f"📈 Максимальный лимит: {stats['max_tokens']:,} токенов")
            
            # Распределение по тарифам
            tariff_distribution = {}
            for info in keys.values():
                name = info.get('name', 'Unknown')
                if name not in tariff_distribution:
                    tariff_distribution[name] = 0
                tariff_distribution[name] += 1
            
            if tariff_distribution:
                print("\n🏷️  Распределение по тарифам:")
                for name, count in sorted(tariff_distribution.items()):
                    print(f"   {name}: {count} ключ(ей)")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


def backup_command(args):
    """Создание резервной копии ключей"""
    try:
        backup_path = args.path or "keys_backup.json"
        success = backup_keys(backup_path)
        
        if success:
            print(f"✅ Резервная копия создана: {backup_path}")
            
            # Показываем статистику резервной копии
            stats = get_keys_stats()
            print(f"   Сохранено ключей: {stats['total_keys']}")
            print(f"   Общий лимит: {stats['total_tokens']:,} токенов")
        else:
            print("❌ Ошибка при создании резервной копии")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


def restore_command(args):
    """Восстановление ключей из резервной копии"""
    try:
        if not Path(args.path).exists():
            print(f"❌ Файл резервной копии не найден: {args.path}")
            sys.exit(1)
        
        # Подтверждение восстановления
        if not args.force:
            current_stats = get_keys_stats()
            print(f"⚠️  Восстановление заменит текущие ключи!")
            print(f"   Текущих ключей: {current_stats['total_keys']}")
            print(f"   Файл резервной копии: {args.path}")
            
            confirm = input("Введите 'yes' для подтверждения: ").strip().lower()
            if confirm != 'yes':
                print("❌ Восстановление отменено")
                return
        
        success = restore_keys(args.path)
        
        if success:
            print(f"✅ Ключи восстановлены из: {args.path}")
            
            # Показываем статистику после восстановления
            stats = get_keys_stats()
            print(f"   Восстановлено ключей: {stats['total_keys']}")
            print(f"   Общий лимит: {stats['total_tokens']:,} токенов")
        else:
            print("❌ Ошибка при восстановлении ключей")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        sys.exit(1)


def update_env_file(api_key):
    """Обновление .env файла с новым API-ключом"""
    try:
        env_path = Path(__file__).parent.parent / ".env"
        
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ищем строку с ALLOWED_API_KEYS
            lines = content.split('\n')
            updated = False
            
            for i, line in enumerate(lines):
                if line.startswith('ALLOWED_API_KEYS='):
                    # Добавляем новый ключ к существующим
                    current_keys = line.split('=', 1)[1]
                    if current_keys and not current_keys.endswith(','):
                        current_keys += ','
                    lines[i] = f"ALLOWED_API_KEYS={current_keys}{api_key}"
                    updated = True
                    break
            
            if updated:
                with open(env_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(lines))
                print(f"✅ Ключ добавлен в .env файл")
            else:
                print("⚠️  Не удалось найти ALLOWED_API_KEYS в .env файле")
        else:
            print("⚠️  .env файл не найден")
            
    except Exception as e:
        print(f"⚠️  Ошибка при обновлении .env файла: {e}")


def main():
    """Главная функция CLI"""
    parser = argparse.ArgumentParser(
        description="CLI-утилита для управления API-ключами и тарифами LLM Gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python tools/cli.py create-key --limit 100000 --name "Premium Plan"
  python tools/cli.py list-keys --stats --verbose
  python tools/cli.py revoke-key --key sk-abc123... --force
  python tools/cli.py set-limit --key sk-abc123... --limit 200000
  python tools/cli.py stats
  python tools/cli.py backup --path my_backup.json
  python tools/cli.py restore --path my_backup.json --force
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Доступные команды')
    
    # Команда create-key
    create_parser = subparsers.add_parser('create-key', help='Создать новый API-ключ')
    create_parser.add_argument('--limit', type=int, required=True, 
                              help='Лимит токенов для ключа')
    create_parser.add_argument('--name', type=str, 
                              help='Название тарифа')
    create_parser.add_argument('--description', type=str, 
                              help='Описание тарифа')
    create_parser.add_argument('--add-to-env', action='store_true',
                              help='Добавить ключ в .env файл')
    
    # Команда revoke-key
    revoke_parser = subparsers.add_parser('revoke-key', help='Удалить API-ключ')
    revoke_parser.add_argument('--key', type=str, required=True,
                              help='API-ключ для удаления')
    revoke_parser.add_argument('--force', action='store_true',
                              help='Удалить без подтверждения')
    
    # Команда list-keys
    list_parser = subparsers.add_parser('list-keys', help='Показать все API-ключи')
    list_parser.add_argument('--stats', action='store_true',
                            help='Показать статистику')
    list_parser.add_argument('--verbose', action='store_true',
                            help='Подробный вывод')
    
    # Команда set-limit
    limit_parser = subparsers.add_parser('set-limit', help='Обновить лимит токенов')
    limit_parser.add_argument('--key', type=str, required=True,
                             help='API-ключ')
    limit_parser.add_argument('--limit', type=int, required=True,
                             help='Новый лимит токенов')
    
    # Команда stats
    stats_parser = subparsers.add_parser('stats', help='Показать статистику')
    
    # Команда backup
    backup_parser = subparsers.add_parser('backup', help='Создать резервную копию')
    backup_parser.add_argument('--path', type=str,
                              help='Путь для резервной копии')
    
    # Команда restore
    restore_parser = subparsers.add_parser('restore', help='Восстановить из резервной копии')
    restore_parser.add_argument('--path', type=str, required=True,
                               help='Путь к резервной копии')
    restore_parser.add_argument('--force', action='store_true',
                               help='Восстановить без подтверждения')
    
    # Парсинг аргументов
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Выполнение команд
    try:
        if args.command == 'create-key':
            create_key_command(args)
        elif args.command == 'revoke-key':
            revoke_key_command(args)
        elif args.command == 'list-keys':
            list_keys_command(args)
        elif args.command == 'set-limit':
            set_limit_command(args)
        elif args.command == 'stats':
            stats_command(args)
        elif args.command == 'backup':
            backup_command(args)
        elif args.command == 'restore':
            restore_command(args)
        else:
            print(f"❌ Неизвестная команда: {args.command}")
            parser.print_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Операция прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()