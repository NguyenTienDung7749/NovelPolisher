from src.chapter_split import split_into_chapters

def test_split_two_chapters():
    """Test splitting text with two chapters."""
    text = """
Chương 1: Thiếu Niên Khởi Hành

Lý Thanh Vân nhìn ra cửa sổ, trời đã sang thu.
Hôm nay là ngày cuối cùng ở nhà.

Chương 2: Gặp Gỡ Tại Kinh Thành

Kinh thành đông đúc, người qua lại tấp nập.
Thanh Vân cảm thấy choáng ngợp.
"""
    print(f"Testing text:\n{text}")
    chapters = split_into_chapters(text)
    
    print(f"Found {len(chapters)} chapters")
    for i, ch in enumerate(chapters):
        print(f"Chapter {ch.number}: {ch.title}")
        print(f"Text: '{ch.text}'")

    if len(chapters) == 2:
        print("✅ Correct number of chapters")
    else:
        print("❌ Incorrect number of chapters")

    if chapters[0].number == 1 and "Lý Thanh Vân" in chapters[0].text:
        print("✅ Chapter 1 OK")
    else:
        print("❌ Chapter 1 Failed")

    if chapters[1].number == 2 and "Kinh thành" in chapters[1].text:
        print("✅ Chapter 2 OK")
    else:
        print("❌ Chapter 2 Failed")

if __name__ == "__main__":
    test_split_two_chapters()
