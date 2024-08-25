import cv2
import face_recognition
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import AuthLog, AuthorizedPerson
from .serializers import AuthLogSerializer
from rest_framework.pagination import PageNumberPagination
import pickle
import os
import time

# Define the path to the encodings.pickle file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENCODINGS_FILE_PATH = os.path.join(BASE_DIR, 'scripts/encodings.pickle')

def read_encodings_file():
    if os.path.isfile(ENCODINGS_FILE_PATH):
        with open(ENCODINGS_FILE_PATH, "rb") as f:
            data = pickle.load(f)
            return data["encodings"], data["names"]
    return [], []

def update_encodings_file(encodings, names):
    with open(ENCODINGS_FILE_PATH, "wb") as f:
        pickle.dump({"encodings": encodings, "names": names}, f)

class AuthenticateView(APIView):
    def get(self, request):
        known_encodings, known_names = read_encodings_file()

        if not known_encodings:
            return Response({'error': 'No authorized persons found'}, status=status.HTTP_400_BAD_REQUEST)

        video_capture = cv2.VideoCapture(0)
        cv2.namedWindow('Camera')

        start_time = time.time()
        best_face_image = None
        max_faces = 0

        while (time.time() - start_time) < 15:
            ret, frame = video_capture.read()
            if not ret:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            if len(face_encodings) > max_faces:
                max_faces = len(face_encodings)
                best_face_image = frame[
                    face_locations[0][0]:face_locations[0][2],
                    face_locations[0][3]:face_locations[0][1]
                ]

            for face_location in face_locations:
                top, right, bottom, left = face_location
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            cv2.imshow('Camera', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

        authenticated = False
        authenticated_name = None

        if best_face_image is not None:
            rgb_face_image = cv2.cvtColor(best_face_image, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_face_image)

            if face_encodings:
                matches = face_recognition.compare_faces(known_encodings, face_encodings[0])
                if True in matches:
                    authenticated = True
                    match_index = matches.index(True)
                    authenticated_name = known_names[match_index]

        result_frame = np.copy(best_face_image) if best_face_image is not None else np.zeros((480, 640, 3), dtype=np.uint8)
        signal_color = (0, 255, 0) if authenticated else (0, 0, 255)
        result_text = "Authenticated" if authenticated else "Not Authenticated"
        cv2.putText(result_frame, result_text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, signal_color, 2, cv2.LINE_AA)

        cv2.imshow('Result', result_frame)
        cv2.waitKey(15000)  # Show result for 15 seconds
        cv2.destroyAllWindows()

        AuthLog.objects.create(authenticated=authenticated)

        return Response({"authenticated": authenticated, "name": authenticated_name})

class RegisterView(APIView):
    def post(self, request):
        name = request.data.get('name')

        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)

        video_capture = cv2.VideoCapture(0)
        cv2.namedWindow('Capture')

        start_time = time.time()
        best_face_image = None
        max_face_size = 0

        while (time.time() - start_time) < 15:  # 15 seconds capture window
            ret, frame = video_capture.read()
            if not ret:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

                face_size = (right - left) * (bottom - top)
                if face_size > max_face_size:
                    max_face_size = face_size
                    best_face_image = frame[top:bottom, left:right]

            cv2.imshow('Capture', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

        if best_face_image is None:
            return Response({'error': 'No face found during the capture period'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rgb_face_image = cv2.cvtColor(best_face_image, cv2.COLOR_BGR2RGB)
            face_encodings = face_recognition.face_encodings(rgb_face_image)

            if not face_encodings:
                return Response({'error': 'No face found in the best captured image'}, status=status.HTTP_400_BAD_REQUEST)

            face_encoding = face_encodings[0]
            serialized_encoding = pickle.dumps(face_encoding)

            known_encodings, known_names = read_encodings_file()
            known_encodings.append(face_encoding)
            known_names.append(name)
            update_encodings_file(known_encodings, known_names)

            AuthorizedPerson.objects.create(name=name, face_encoding=serialized_encoding)
            return Response({'success': f'Successfully added {name} to authorized persons'}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DeleteView(APIView):
    def delete(self, request):
        name = request.data.get('name')

        if not name:
            return Response({"error": "Name is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            person = AuthorizedPerson.objects.get(name=name)
            person.delete()

            known_encodings, known_names = read_encodings_file()
            if name in known_names:
                index = known_names.index(name)
                known_encodings.pop(index)
                known_names.pop(index)
                update_encodings_file(known_encodings, known_names)

            return Response({"message": f"Successfully deleted {name}"}, status=status.HTTP_200_OK)
        except AuthorizedPerson.DoesNotExist:
            return Response({"error": "Person not found"}, status=status.HTTP_404_NOT_FOUND)

class AuthLogView(APIView):
    def get(self, request):
        page_size = int(request.query_params.get('page_size', 10))
        page = int(request.query_params.get('page', 1))
        
        logs = AuthLog.objects.all().order_by('-timestamp')
        
        paginator = PageNumberPagination()
        paginator.page_size = page_size
        result_page = paginator.paginate_queryset(logs, request)
        
        serializer = AuthLogSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)