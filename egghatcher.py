import asyncio
import time

from PIL import Image
import yaml


from pyocr import pyocr
from pyocr import builders
from ADBlib import ADBlib



def get_median_location(box_location):
    x1, y1, x2, y2 = box_location
    return [int((x1 + x2) / 2), int((y1 + y2) / 2)]


class Main:
    def __init__(self):
        with open("config.yaml", "r") as f:
            self.config = yaml.load(f, Loader=yaml.FullLoader)
        tools = pyocr.get_available_tools()
        self.tool = tools[0]
        self.state = ''
        self.egg_walked = 0
        self.distance_total = 0
        self.distance_walked = 0

    async def tap(self, location):
        coordinates = self.config['locations'][location]
        if len(coordinates) == 2:
            await self.p.tap(*coordinates)
            if location in self.config['waits']:
                await asyncio.sleep(self.config['waits'][location])
        elif len(coordinates) == 4:
            median_location = get_median_location(coordinates)
            await self.p.tap(*median_location)
            if location in self.config['waits']:
                await asyncio.sleep(self.config['waits'][location])

    async def cap_and_crop(self, box_location):
        screencap = await self.p.screencap()
        crop = screencap.crop(self.config['locations'][box_location])
        text = self.tool.image_to_string(crop).replace("\n", " ")
        return text


    #map/eggs/menu/hatching
    async def get_current_state(self):
        screencap = await self.p.screencap()
        text_eggs = screencap.crop(self.config['locations']['eggs_label_box'])
        text_eggs = self.tool.image_to_string(text_eggs).replace("\n", " ")
        if 'EGGS' in text_eggs:
            return 'on_eggs'

        text_menu = screencap.crop(self.config['locations']['settings_button_box'])
        text_menu = self.tool.image_to_string(text_menu).replace("\n", " ")
        if 'SETTINGS' in text_menu:
            return 'on_menu'

        text_oh = screencap.crop(self.config['locations']['oh_hatching_box'])
        text_oh = self.tool.image_to_string(text_oh).replace("\n", " ")
        if 'Oh' in text_oh or '?' in text_oh:
            return 'on_hatching'

        return 'on_world'

    #app resi

    async def stopPGO(self):
        await self.p.run("adb shell am force-stop com.nianticlabs.pokemongo")
        await self.p.run("adb shell monkey -p com.fitness.debugger -c android.intent.category.LAUNCHER 1")

    async def startPGO(self):
        await self.p.run("adb shell monkey -p com.nianticlabs.pokemongo -c android.intent.category.LAUNCHER 1")
        await self.p.run("adb shell am force-stop com.fitness.debugger")
        
        await asyncio.sleep(30)
        await self.tap('im_a_passenger_button_box')



    async def checkDefitTime(self):
        await self.check_my_eggs()
        remainingKM = self.distance_total - self.distance_walked
        remainingTime = 6.7 * remainingKM * 60
        remainingTime = round(remainingTime)
        print(remainingKM,remainingTime)
        return(remainingKM, remainingTime)
    #Tojás cuccok
    async def incubate_a_lovely_egg(self):
        await self.tap('first_egg_distance_box')
        text = await self.cap_and_crop('incubate_button_box')

        if 'INCUBATE' in text.replace(" ","" ):
            print('Ez a tojás még nem megy!')
            await self.tap('incubate_button_box')
            print('Első tojás...')
            await self.tap('incubator_uses_left_box')
        else:
            print('Ez a tojás már megy!')
            await self.tap('pokeball_button')

    async def watch_the_egg_hatch(self):
        print('Végre kikelt egy tojgli!')
        await self.tap('im_a_passenger_button_box')
        await asyncio.sleep(20)
        await self.tap('pokeball_button')
        await self.tap('pokeball_button')
        self.egg_walked += 1
        print("Eddíg {} tojást keltettél ki.".format(self.egg_walked))

    async def check_my_eggs(self):
        print("Nézzük csak a tojásokat! \n               ... Gotta Check 'em All! ♫ ...")

        await self.tap('pokeball_button')
        
        if not await self.get_current_state() == 'on_menu':
            print('Valami baj van, nem lép tovább a menüre')
            return False

        await self.tap('pokemon_list_button')
        await self.tap('eggs_tab')

        text = await self.cap_and_crop('first_egg_distance_box')

        try:
            self.distance_walked, self.distance_total = [float(d) for d in text.replace('km', '').replace('O', '0').split('/')]
        except:
            print("Lol valamit félrenéztem! (Ezt olvastam \"" + text + '")')
            return False

        if self.distance_walked == 0 and self.distance_walked < self.distance_total:
            await self.incubate_a_lovely_egg()

        elif self.distance_walked == self.distance_total == 0:
            await self.check_my_eggs()
            self.state = 'on_hatching'

        text = await self.cap_and_crop('first_egg_distance_box')

        try:
            self.distance_walked, self.distance_total = [float(d) for d in text.replace('km', '').replace('O', '0').split('/')]
        except:
            print("Lol valamit félrenéztem! (Ezt olvastam \"" + text + '")')
            return False

        print('Eddíg {}kmt "sétáltál" egy {}kmes tojáshoz'.format(self.distance_walked, self.distance_total))


        await self.tap('pokeball_button')
        return True


    async def start(self):

        self.p = ADBlib()
        timeNow = round(time.time())
        nextCheckTime = timeNow + 10
        lol = False
        while True:
            await asyncio.sleep(1)
            print(nextCheckTime - timeNow)
            timeNow = round(time.time())
            if timeNow != nextCheckTime: continue
            
            if lol: 
                await self.startPGO()
            lol = True
            self.state = await self.get_current_state()

            if self.state == 'on_hatching':
                await self.watch_the_egg_hatch()
            elif self.state == 'on_world':
                pass
            elif self.state == 'on_eggs':
                await self.tap('pokeball_button')

            a,b = await self.checkDefitTime()
            nextCheckTime += b
            await self.stopPGO()
            



if __name__ == '__main__':
    asyncio.run(Main().start())
