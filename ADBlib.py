from PIL import Image
import asyncio
import subprocess


class ADBlib(object):
    async def screencap(self):
        await self.run("adb shell screencap -p /sdcard/screen.png")
        await self.run("adb pull /sdcard/screen.png .")
        image = Image.open("screen.png")
        return image

    async def run(self, args):
        args = args.split(" ")
        p = subprocess.Popen(args)
        stdout, stderr = p.communicate()
        return (stdout, stderr)

    async def tap(self, x, y):
        await self.run("adb shell input tap {} {} ".format(x,y))

    async def swipe(self, x1, y1, x2, y2, duration=None):
        args = "adb shell input swipe {} {} {} {} ".format(x1,y1,x2,y2)

        if duration:
            args += duration

        await self.run(args)

