import os
import subprocess
from django.conf import settings
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
import pytz
from .forms import ImagenForm, RegistroForm, ProfileForm, UserForm
from .models import Imagen, Profile
import hashlib
from django.core.files.storage import default_storage
from django.contrib.auth.views import PasswordResetCompleteView
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.paginator import Paginator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from io import BytesIO
from .models import Historial
from inference_sdk import InferenceHTTPClient
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import hashlib
import pytz
import cv2
import numpy as np
import requests
from django.http import HttpResponse
import tempfile


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    def get(self, request, *args, **kwargs):
        return redirect('login')
    

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Perfil actualizado exitosamente')
            return redirect('profile')
        
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)

    return render(request, 'editar_perfil.html', {'user_form': user_form, 'profile_form': profile_form})


def guardar_resultados(request):
    if request.method == 'POST':
        historial = Historial(
            user=request.user,
            paciente_nombre=request.POST.get('paciente_nombre'),
            imagen=request.FILES.get('imagen'),
            porcentaje=request.POST.get('porcentaje'),
            grupo=request.POST.get('grupo'),
            pdf_url=request.POST.get('pdf_url')
        )
        historial.save()
        return redirect('resultados')
    
@login_required
def historial_medico(request):
    historial = Historial.objects.filter(user=request.user).order_by('-fecha_imagen')
    # context = {
    #     'historial': historial
    # }
    paginator = Paginator(historial, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'historial_medico.html',{'page_obj': page_obj})

@login_required
def historial_medico_general(request):

    historial = Historial.objects.all().order_by('-fecha_imagen')

    paginator = Paginator(historial, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj
    }
    
    return render(request, 'historial_medico_general.html', context)

@login_required
def eliminar_historial_general(request, id):
    historial_item = get_object_or_404(Historial, id=id)

    if request.method == "POST":

        if historial_item.imagen:
            historial_item.imagen.delete()  
        
        historial_item.delete()
        messages.success(request, 'El registro ha sido eliminado correctamente.')

    return redirect('historial_med_gene')

@login_required
def eliminar_historial(request, id):
    historial_item = get_object_or_404(Historial, id=id, user=request.user)

    if request.method == "POST":
        if historial_item.imagen:
            historial_item.imagen.delete()
        
        historial_item.delete()
        messages.success(request, 'El registro ha sido eliminado correctamente.')

    return redirect('historial_med')

@login_required
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def index(request):
    
    if not request.session.get('welcome_message_shown', False):
        request.session['welcome_message_shown'] = True
        show_welcome_message = True
    else:
        show_welcome_message = False

    return render(request, 'home.html', {
        'user': request.user,
        'show_welcome_message': show_welcome_message,
    })
    
    
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Nombre de usuario o contraseña incorrectos.')
    return render(request, 'login.html')



@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)  
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)  

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)

    return render(request, 'perfil.html', {'user_form': user_form, 'profile_form': profile_form})


def password_reset_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            messages.success(request, 'Se ha enviado un enlace para restablecer la contraseña a tu correo electrónico.')
            return redirect('password_reset')
        except User.DoesNotExist:
            messages.error(request, 'El correo electrónico no está registrado en nuestro sistema.')
    return render(request, 'password_reset.html')


def generar_pdf_general(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    if request.user.is_superuser:
        historiales = Historial.objects.all()
    else:
        historiales = Historial.objects.filter(user=request.user)

    titulo_color = HexColor('#4A90E2')  
    texto_color = HexColor('#333333')  
    imagen_fondo_color = HexColor('#F0F0F0') 

    items_por_pagina = 0
    posiciones_y = [height - 1.5 * inch, height - 7 * inch]  

    ecuador_tz = pytz.timezone('America/Guayaquil')  

    for index, item in enumerate(historiales):
        if items_por_pagina == 2:
            p.showPage()
            items_por_pagina = 0  

        y_position = posiciones_y[items_por_pagina]

        p.setFont("Helvetica-Bold", 16)
        p.setFillColor(titulo_color)
        p.drawString(1 * inch, y_position + 0.5 * inch, "Historial Médico del Usuario")

        p.setFillColor(texto_color)
        p.line(0.5 * inch, y_position + 0.2 * inch, width - 0.5 * inch, y_position + 0.2 * inch)

        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, y_position - 0.5 * inch, "Nombre del Doctor:")
        p.setFont("Helvetica", 12)
        p.drawString(3 * inch, y_position - 0.5 * inch, item.user.username)

        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, y_position - 1 * inch, "Nombre del Paciente:")
        p.setFont("Helvetica", 12)
        p.drawString(3 * inch, y_position - 1 * inch, item.paciente_nombre)

        # Convierte la fecha de UTC a la zona horaria de Guayaquil
        fecha_imagen_local = item.fecha_imagen.astimezone(ecuador_tz)

        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, y_position - 1.5 * inch, "Fecha:")
        p.setFont("Helvetica", 12)
        p.drawString(3 * inch, y_position - 1.5 * inch, fecha_imagen_local.strftime('%d-%m-%Y'))

        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, y_position - 2 * inch, "Hora:")
        p.setFont("Helvetica", 12)
        p.drawString(3 * inch, y_position - 2 * inch, fecha_imagen_local.strftime('%H:%M:%S'))

        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, y_position - 2.5 * inch, "Porcentaje:")
        p.setFont("Helvetica", 12)
        p.drawString(3 * inch, y_position - 2.5 * inch, f"{item.porcentaje}%")

        p.setFont("Helvetica-Bold", 12)
        p.drawString(1 * inch, y_position - 3 * inch, "Tipo de Hernia:")
        p.setFont("Helvetica", 12)
        p.drawString(3 * inch, y_position - 3 * inch, item.grupo)

        if item.imagen:
            p.setFillColor(imagen_fondo_color)
            p.rect(5 * inch - 0.1 * inch, y_position - 3.5 * inch - 0.1 * inch, 2.7 * inch, 3.2 * inch, fill=1)

            image_url = item.imagen.url
            response = requests.get(image_url)

            if response.status_code != 200:
                p.drawString(5 * inch, y_position - 1.5 * inch, "Imagen no disponible")
                items_por_pagina += 1
                continue  

            if not response.content:
                p.drawString(5 * inch, y_position - 1.5 * inch, "Imagen no disponible")
                items_por_pagina += 1
                continue  

            try:
                image_data = BytesIO(response.content)
                img = Image.open(image_data)
                img_rgb = img.convert('RGB')
            except Exception as e:
                p.drawString(5 * inch, y_position - 1.5 * inch, "Error al cargar la imagen")
                items_por_pagina += 1
                continue  

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                img_rgb.save(temp_file, format='JPEG')
                temp_file_path = temp_file.name  

            p.drawImage(temp_file_path, 5 * inch, y_position - 3.5 * inch, width=2.5 * inch, height=3 * inch, mask='auto')

            os.remove(temp_file_path)
        else:
            p.drawString(5 * inch, y_position - 1.5 * inch, "Imagen no disponible")

        items_por_pagina += 1

    p.save()

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    if request.user.is_superuser:
        response['Content-Disposition'] = 'attachment; filename="historial_medico_todos_usuarios.pdf"'
    else:
        response['Content-Disposition'] = f'attachment; filename="historial_medico_{request.user.username}.pdf"'
    return response



def generar_pdf_fila(request, id):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    item = get_object_or_404(Historial, id=id)

    titulo_color = HexColor('#4A90E2')
    texto_color = HexColor('#333333')
    imagen_fondo_color = HexColor('#F0F0F0')

    ecuador_tz = pytz.timezone('America/Guayaquil')
    fecha_imagen_local = item.fecha_imagen.astimezone(ecuador_tz)

    p.setFont("Helvetica-Bold", 20)
    p.setFillColor(titulo_color)
    p.drawString(2 * inch, height - 1 * inch, "Historial Médico del Usuario")
    
    p.setFillColor(texto_color)
    p.line(0.5 * inch, height - 1.2 * inch, width - 0.5 * inch, height - 1.2 * inch)

    line_height = 0.4 * inch
    y_position = height - 1.5 * inch

    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, y_position, "Nombre del Doctor:")
    p.setFont("Helvetica", 12)
    p.drawString(3 * inch, y_position, item.user.username)  
    y_position -= line_height

    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, y_position, "Nombre del Paciente:")
    p.setFont("Helvetica", 12)
    p.drawString(3 * inch, y_position, item.paciente_nombre)  
    y_position -= line_height

    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, y_position, "Fecha:")
    p.setFont("Helvetica", 12)
    p.drawString(3 * inch, y_position, fecha_imagen_local.strftime('%d-%m-%Y'))  
    y_position -= line_height

    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, y_position, "Hora:")
    p.setFont("Helvetica", 12)
    p.drawString(3 * inch, y_position, fecha_imagen_local.strftime('%H:%M:%S'))  
    y_position -= line_height
    
    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, y_position, "Porcentaje:")
    p.setFont("Helvetica", 12)
    p.drawString(3 * inch, y_position, f"{item.porcentaje}%") 
    y_position -= line_height

    p.setFont("Helvetica-Bold", 12)
    p.drawString(1 * inch, y_position, "Tipo de Hernia:")
    p.setFont("Helvetica", 12)
    p.drawString(3 * inch, y_position, item.grupo)  
    y_position -= line_height

    if item.imagen:
        p.setFillColor(imagen_fondo_color)
        p.rect(5 * inch - 0.1 * inch, height - 4.5 * inch - 0.1 * inch, 2.7 * inch, 3.2 * inch, fill=1)

        image_url = item.imagen.url
        response = requests.get(image_url)

        if response.status_code == 200 and response.content:
            try:
                image_data = BytesIO(response.content)
                img = Image.open(image_data)
                img_rgb = img.convert('RGB')

                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                    img_rgb.save(temp_file, format='JPEG')
                    temp_file_path = temp_file.name  

                p.drawImage(temp_file_path, 5 * inch, height - 4.5 * inch, width=2.5 * inch, height=3 * inch, mask='auto')
                os.remove(temp_file_path)
            except Exception as e:
                p.drawString(5 * inch, height - 5 * inch, "Error al cargar la imagen")
        else:
            p.drawString(5 * inch, height - 5 * inch, "Imagen no disponible")
    else:
        p.drawString(5 * inch, height - 5 * inch, "Imagen no disponible")

    p.showPage()
    p.save()

    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="historial_medico_fila.pdf"'
    return response




# Configurar el cliente de Roboflow
CLIENT = InferenceHTTPClient(
    api_url="https://outline.roboflow.com",
    api_key="8HZzIhc5cRGKVeheO0R7"
)

def subir_imagen(request):
    if request.method == 'POST':
        form = ImagenForm(request.POST, request.FILES)
        if form.is_valid():
            imagen_obj = form.save(commit=False)
            paciente_nombre = form.cleaned_data.get('paciente_nombre')
            original_name = request.FILES['imagen'].name
            hash_object = hashlib.sha256(original_name.encode())
            encrypted_name = hash_object.hexdigest() + '.' + original_name.split('.')[-1]
            imagen_obj.imagen.name = encrypted_name
            
            imagen_obj.paciente_nombre = paciente_nombre
            imagen_obj.save()

            image_url = imagen_obj.imagen.url
            response = requests.get(image_url)
            image_data = BytesIO(response.content)

            image_pil = Image.open(image_data).convert('RGB')
            img_cv2 = np.array(image_pil)
            img_cv2 = cv2.cvtColor(img_cv2, cv2.COLOR_RGB2BGR)

            result = CLIENT.infer(image_url, model_id="proy_2/1")
            predictions = result.get('predictions', [])

            for pred in predictions:

                confidence = pred['confidence'] * 100  
                class_name = pred['class']


                if 'points' in pred:
                    points = np.array([[p['x'], p['y']] for p in pred['points']], dtype=np.int32)

                    overlay = img_cv2.copy()
                    cv2.fillPoly(overlay, [points], (0, 0, 255))  
                    alpha = 0.4 
                    cv2.addWeighted(overlay, alpha, img_cv2, 1 - alpha, 0, img_cv2)

                    color = (0, 255, 0) if class_name == 'Sin Hernia' else (255, 0, 0)
                    cv2.polylines(img_cv2, [points], isClosed=True, color=color, thickness=2)

                    x_min = min(points[:, 0])
                    y_min = min(points[:, 1])
                    text = f"{class_name} {confidence:.2f}%"
                    cv2.putText(img_cv2, text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            img_pil_final = Image.fromarray(cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB))
            buffer = BytesIO()
            img_pil_final.save(buffer, format="JPEG")
            buffer.seek(0)

            imagen_obj.imagen.save(encrypted_name, buffer)

            if result['predictions'] and result['predictions'][0]['class']:
                class_prediction = result['predictions'][0]['class']
                if class_prediction == 'Sin Hernia':
                    grupo = "Sin Hernia"
                    print("El diagnóstico es Sin hernia.")
                elif class_prediction == 'Hernia':
                    grupo = "Hernia"
                    print("El diagnóstico es una Hernia.")
            else:
                grupo = "Predicción no encontrada."
                print("El diagnóstico no es válido.")

            porcentaje = round(result['predictions'][0]['confidence'] * 100, 2) if result['predictions'] else 0
            
            
            ecuador_tz = pytz.timezone('America/Guayaquil')
            fecha_imagen_local = imagen_obj.fecha.astimezone(ecuador_tz)
            
            historial = Historial(
                user=request.user,
                imagen=imagen_obj.imagen,
                porcentaje=porcentaje,
                grupo=grupo,
                paciente_nombre=paciente_nombre,
                fecha_imagen=fecha_imagen_local,
            )
            historial.save()

            

            context = {
                'grupo': grupo,
                'porcentaje': porcentaje,
                'original_image_url': image_url,
                'processed_image_url': imagen_obj.imagen.url,
                'fecha_imagen': fecha_imagen_local,
                'paciente_nombre': paciente_nombre
            }

            return render(request, 'resultados.html', context)
    else:
        form = ImagenForm()

    return render(request, 'subir_imagen.html', {'form': form})


def register_view(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, '¡Registro exitoso! Por favor, inicia sesión.')
                # return redirect('login') 
            except Exception as e:
                messages.error(request, f'Error al registrar el usuario: {e}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = RegistroForm()
    
    return render(request, 'register.html', {'form': form})

@login_required
def resultados(request):
    return render(request, 'resultados.html')

@login_required
def user_profile_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    if profile is None:
        profile = Profile.objects.create(user=user)

    return render(request, 'perfil.html', {'user': user, 'profile': profile})


