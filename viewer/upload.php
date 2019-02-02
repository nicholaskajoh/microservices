<?php
    require_once 'vendor/autoload.php';

    // $dotenv = Dotenv\Dotenv::create(__DIR__);
    // $dotenv->load();

    \Cloudinary::config(array(
        'cloud_name' => getenv('CLOUDINARY_CLOUD_NAME'), 
        'api_key' => getenv('CLOUDINARY_API_KEY'), 
        'api_secret' => getenv('CLOUDINARY_API_SECRET'),
    ));

    if (is_uploaded_file($_FILES['input_image']['tmp_name'])) {
        // upload image to Cloudinary
        $image = \Cloudinary\Uploader::upload($_FILES['input_image']['tmp_name'], array(
            'folder' => 'detector_svc_images/inputs',
        ));

        // make post request to detector service
        $url = getenv('DETECTOR_SVC_URL');    
        $content = json_encode(array('image_url' => $image['url']));
        $curl = curl_init($url);
        curl_setopt($curl, CURLOPT_HEADER, false);
        curl_setopt($curl, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($curl, CURLOPT_HTTPHEADER, array('Content-type: application/json'));
        curl_setopt($curl, CURLOPT_POST, true);
        curl_setopt($curl, CURLOPT_POSTFIELDS, $content);
        $json_response = curl_exec($curl);
        $status = curl_getinfo($curl, CURLINFO_HTTP_CODE);
        if ($status != 200) {
            header('Location: /?processed=0');
            exit();
        }
        curl_close($curl);
        $response = json_decode($json_response, true);

        // store response in redis
        $redis = new Predis\Client(getenv('REDIS_URL'));
        $image_id = uniqid();
        $redis->lpush("image_ids", $image_id);
        $redis->set('image_url_' . $image_id, $response['url']);
        $redis->hmset('image_objects_' . $image_id, $response['objects']);

        header('Location: /?new_output=1');
    } else {
        header('Location: /?input_image=0'); 
    }
    exit();