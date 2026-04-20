import os
import argparse
from PIL import Image, ImageFilter
from io import BytesIO


def print_compression_info(filename, original_size, final_size, quality, target_size_mb, success=True):
    compression_pct = (1 - final_size / original_size) * 100
    size_note = "" if success else f", всё ещё >{target_size_mb} МБ"
    print(f"{filename} | {original_size // 1024} КБ → {final_size // 1024} КБ | Качество: {quality} ({compression_pct:.1f}% сжатия{size_note})")


def copy_file_time(src_path, dst_path):
    stat = os.stat(src_path)
    os.utime(dst_path, (stat.st_atime, stat.st_mtime))


def find_optimal_quality(img, exif, target_size_bytes, min_quality=10, max_quality=95):
    low, high = min_quality, max_quality
    best_quality = min_quality
    best_buffer = None

    while low <= high:
        mid = (low + high) // 2

        use_img = img.filter(ImageFilter.SMOOTH) if mid < 70 else img

        buffer = BytesIO()
        if exif:
            use_img.save(buffer, "JPEG", quality=mid, optimize=True, exif=exif)
        else:
            use_img.save(buffer, "JPEG", quality=mid, optimize=True)

        if buffer.tell() <= target_size_bytes:
            best_quality = mid
            best_buffer = buffer
            low = mid + 1
        else:
            high = mid - 1

    return best_quality, best_buffer


def compress_images_in_folder(folder_path, prefix="compressed_", target_size_mb=1.0, target_quality=50):
    target_size_bytes = int(target_size_mb * 1024 * 1024)

    for filename in os.listdir(folder_path):
        if filename.lower().endswith(('.jpg', '.jpeg')):
            input_path = os.path.join(folder_path, filename)
            output_path = os.path.join(folder_path, prefix + filename)

            with Image.open(input_path) as img:
                original_size = os.path.getsize(input_path)
                exif = img.info.get('exif')

                best_quality, best_buffer = find_optimal_quality(
                    img, exif, target_size_bytes,
                    min_quality=target_quality,
                    max_quality=95
                )

                # Гарантируем, что best_buffer существует
                if best_buffer is None:
                    # На всякий случай — создадим с минимальным качеством
                    use_img = img.filter(
                        ImageFilter.SMOOTH) if target_quality < 70 else img
                    best_buffer = BytesIO()
                    if exif:
                        use_img.save(
                            best_buffer, "JPEG", quality=target_quality, optimize=True, exif=exif)
                    else:
                        use_img.save(best_buffer, "JPEG",
                                     quality=target_quality, optimize=True)

                if best_buffer.tell() <= target_size_bytes:
                    with open(output_path, "wb") as f:
                        f.write(best_buffer.getvalue())
                    copy_file_time(input_path, output_path)
                    print_compression_info(filename, original_size, best_buffer.tell(
                    ), best_quality, target_size_mb, success=True)
                else:
                    with open(output_path, "wb") as f:
                        f.write(best_buffer.getvalue())
                    copy_file_time(input_path, output_path)
                    print_compression_info(filename, original_size, best_buffer.tell(
                    ), best_quality, target_size_mb, success=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Сжатие JPEG-изображений до заданного размера")
    parser.add_argument("folder", nargs="?", default=".",
                        help="Путь к папке с изображениями (по умолчанию: текущая папка)")
    parser.add_argument("--prefix", default="compressed_",
                        help="Префикс для сжатых файлов (по умолчанию: compressed_)")
    parser.add_argument("--size", type=float, default=1.0,
                        help="Целевой размер в МБ (по умолчанию: 1.0)")
    parser.add_argument("--quality", type=int, default=50,
                        help="Минимальное качество (по умолчанию: 50)")

    args = parser.parse_args()

    folder_path = os.path.abspath(args.folder)
    if not os.path.isdir(folder_path):
        print(f"Ошибка: папка не найдена — {folder_path}")
        exit(1)

    compress_images_in_folder(
        folder_path=folder_path,
        prefix=args.prefix,
        target_size_mb=args.size,
        target_quality=args.quality
    )
