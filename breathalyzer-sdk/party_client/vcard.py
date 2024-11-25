import vobject
import base64
from party_client.globals import phone_numbers


class VCardCreator:
    def __init__(self, name, phone_number, photo_path):
        self.name = name
        self.phone_number = phone_number
        self.photo_path = photo_path

    def create_vcard(self):
        # Create a new vCard
        vcard = vobject.vCard()

        # Add the name
        vcard.add("fn")
        vcard.fn.value = self.name

        # Add a structured name
        vcard.add("n")
        vcard.n.value = vobject.vcard.Name(family="", given=self.name)

        # Add the phone number
        vcard.add("tel")
        vcard.tel.value = self.phone_number
        vcard.tel.type_param = "CELL"

        # Add the profile photo
        with open(self.photo_path, "rb") as photo_file:
            photo_data = base64.b64encode(photo_file.read()).decode("utf-8")

        vcard.add("photo")
        vcard.photo.value = photo_data
        vcard.photo.type_param = "JPEG"
        vcard.photo.encoding_param = "BASE64"  # Ensure proper encoding format

        return vcard

    def save_vcard(self, file_name):
        vcard = self.create_vcard()
        with open(file_name, "w") as vcard_file:
            vcard_file.write(vcard.serialize())
        print(f"vCard with profile photo created successfully as '{file_name}'")


# Usage example
name = "Trick or Drink"
phone_number = phone_numbers["backend_number"]
photo_path = "spooky.jpg"

vcard_creator = VCardCreator(name, phone_number, photo_path)
vcard_creator.save_vcard("trick_or_drink.vcf")
