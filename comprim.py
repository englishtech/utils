import os
import argparse
from PIL import Image, ImageFilter
from io import BytesIO


def print_compression_info(filename, original_size, final_size, target_size_mb, success=True):
    compression_pct = (1 - final_size / original_size) * 100
    status = "Сжат" if success else "Внимание"
    size_note = "" if success else f", всё ещё >{target_size_mb} МБ"
    print(f"{status}: {filename} | Было: {original_size // 1024} КБ → Стало: {final_size // 1024} КБ ({compression_pct:.1f}% сжатия{size_note})")


def copy_file_time(src_path, dst_path):
    """Копирует atime и mtime из src_path в dst_path"""
    stat = os.stat(src_path)
    os.utime(dst_path, (stat.st_atime, stat.st_mtime))


def compress_images_in_folder(folder_path, prefix="compressed_", target_size_mb=1.0, target_quality=50):
    target_size_bytes = int(target_size_mb * 1024 * 1024)

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.jpeg')):
            input_path = os.path.join(folder_path, filename)

            # Пропускаем файлы, уже меньшие цели
            if os.path.getsize(input_path) < target_size_bytes:
                print(f"Пропущен: {filename} (уже < {target_size_mb} МБ)")
                continue

            output_path = os.path.join(folder_path, prefix + filename)

            with Image.open(input_path) as img:
                original_size = os.path.getsize(input_path)
                exif = img.info.get('exif')
                quality = 95
                while quality >= target_quality:
                    buffer = BytesIO()

                    filtered_img = img.filter(
                        ImageFilter.SMOOTH) if quality < 70 else img

                    if exif:
                        filtered_img.save(
                            buffer, "JPEG", quality=quality, optimize=True, exif=exif)
                    else:
                        filtered_img.save(
                            buffer, "JPEG", quality=quality, optimize=True)

                    if buffer.tell() <= target_size_bytes:
                        with open(output_path, "wb") as f:
                            f.write(buffer.getvalue())
                        copy_file_time(input_path, output_path)
                        print_compression_info(
                            filename, original_size, buffer.tell(), target_size_mb, success=True)
                        break

                    quality -= 5
                else:
                    with open(output_path, "wb") as f:
                        f.write(buffer.getvalue())
                    copy_file_time(input_path, output_path)
                    print_compression_info(
                        filename, original_size, buffer.tell(), target_size_mb, success=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Сжатие JPEG-изображений до заданного размера")
    parser.add_argument("folder", help="Путь к папке с изображениями")
    parser.add_argument("--prefix", default="compressed_",
                        help="Префикс для сжатых файлов (по умолчанию: compressed_)")
    parser.add_argument("--size", type=float, default=1.0,
                        help="Целевой размер в МБ (по умолчанию: 1.0)")
    parser.add_argument("--quality", type=int, default=50,
                        help="Минимальное качество (по умолчанию: 50)")

    args = parser.parse_args()

    compress_images_in_folder(
        folder_path=args.folder,
        prefix=args.prefix,
        target_size_mb=args.size,
        target_quality=args.quality
    )
