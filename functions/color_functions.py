from PIL import Image
from io import BytesIO
import aiohttp


class Colors:
    def __init__(self):
        pass

    @staticmethod
    async def get_bytes(img):
        async with aiohttp.ClientSession() as session:
            async with session.get(img) as response:
                return await response.read()

    async def compute_average_image_color(self, img):
        img = await self.get_bytes(img)
        with Image.open(BytesIO(img)).convert("RGB") as img:
            img = img.resize((50, 50))  # Small optimization
            width, height = img.size
            r_total = 0
            g_total = 0
            b_total = 0
            count = 0
            for x in range(0, width):
                for y in range(0, height):
                    r, g, b = img.getpixel((x, y))
                    r_total += r
                    g_total += g
                    b_total += b
                    count += 1
        red = round(r_total/count)
        green = round(g_total/count)
        blue = round(b_total/count)
        hex_ = '#%02x%02x%02x' % (red, green, blue)
        return {"colors": {"red": red, "green": green, "blue": blue},
                "hex": hex_}
