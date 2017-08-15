import os
import docker
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from docker import APIClient
from io import BytesIO
import json
from django.http import JsonResponse, HttpResponseServerError

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

client = docker.from_env()


@require_http_methods(["POST"])
@csrf_exempt
def create_image(request, model):

    if not request.POST.get('path'):
        path = '/Users/lorenamesa/Desktop/djangocon/model/Dockerfile' # BASE_DIR
    else:
        path = request.POST['path']

    with open(path, 'r') as d:
        dockerfile = [x.strip() for x in d.readlines()]
        dockerfile = '\n'.join(dockerfile)

    f = BytesIO(dockerfile.encode('utf-8'))

    # Point to the Docker instance
    cli = APIClient(base_url='unix://var/run/docker.sock')

    try:
        response = cli.build(fileobj=f, rm=True, tag=model + ':latest', stream=True, timeout=60*60)
    except Exception as e:
        return HttpResponseServerError()

    for line in response:
        try:

            stream_line = json.loads(line.decode('utf-8'))
            print_line = ''
            if stream_line.get('status'):
                print_line += stream_line['status'] + ' '
            if stream_line.get('progress'):
                print_line += stream_line['progress']
            print(print_line)

            if stream_line.get('errorDetail'):
                error = stream_line.get('errorDetail')
                return JsonResponse({'error': error})

        except ValueError as e:

            # Some logic to figure out with this is
            # But for now, let's print

            print(line)
            continue

    return JsonResponse({'image': response})


@require_http_methods(["POST"])
@csrf_exempt
def create_container(request):

    if not request.POST.get('code'):
        return HttpResponseServerError()

    else:
        code = request.POST.get['code']

    client.create_container(
       image='python:3',
       command=['python','-c', 'my_code.py'],
       volumes=['/opt'],
       host_config=client.create_host_config(
           binds={
               os.getcwd():
                   {
                       'bind': '/opt',
                       'mode': 'rw',
                   }
           }
       ),
       name='predicting-altruism',
       working_dir='/opt'
    )


def run_container(request):
    client.containers.run("predicting-altruism", detach=True)
    return None