import face_recognition
import pickle
from django.core.management.base import BaseCommand
from auth_app.models import AuthorizedPerson

class Command(BaseCommand):
    help = 'Add an authorized person'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str)
        parser.add_argument('image_path', type=str)

    def handle(self, *args, **options):
        name = options['name']
        image_path = options['image_path']

        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) == 0:
            self.stdout.write(self.style.ERROR(f'No face found in the image for {name}'))
            return
        
        face_encoding = face_encodings[0]
        serialized_encoding = pickle.dumps(face_encoding)
        
        AuthorizedPerson.objects.create(name=name, face_encoding=serialized_encoding)
        
        self.stdout.write(self.style.SUCCESS(f'Successfully added {name} to authorized persons'))