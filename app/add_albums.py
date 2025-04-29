from database import SessionLocal, Album
from datetime import datetime
import json


def add_albums_from_json(filename='albums.json'):
    db = SessionLocal()
    added_count = 0

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            albums_data = json.load(f)

        if not isinstance(albums_data, list):
            print("Ошибка: файл должен содержать массив альбомов")
            return

        for album in albums_data:
            try:
                # Проверяем обязательные поля с учетом вашего формата
                if not all(key in album for key in ['album_title', 'artist_name', 'release_date']):
                    print(f"Пропущен альбом с неполными данными: {album}")
                    continue

                # Преобразуем строку даты
                try:
                    release_date = datetime.strptime(album['release_date'], '%Y-%m-%d').date()
                except ValueError:
                    print(f"Некорректный формат даты в альбоме {album.get('album_title')}")
                    release_date = None

                # Создаем запись альбома
                db_album = Album(
                    album_title=album['album_title'],
                    artist_name=album['artist_name'],
                    release_date=release_date,
                    cover_url=album.get('cover_url'),
                    genre=album.get('genre', 'Unknown')
                )

                db.add(db_album)
                db.commit()
                added_count += 1

            except Exception as e:
                db.rollback()
                print(f"Ошибка при добавлении альбома {album.get('album_title', 'Unknown')}: {str(e)}")
                continue

    except Exception as e:
        print(f"Критическая ошибка: {str(e)}")
    finally:
        db.close()

    print(f"Успешно добавлено {added_count} альбомов из {len(albums_data)}")


if __name__ == '__main__':
    add_albums_from_json()