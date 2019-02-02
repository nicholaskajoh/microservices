<!DOCTYPE html>
<html lang="en">
<head>
    <title>Yoloo</title>
</head>
<body>
    <h1>Yoloo</h1>

    <?php if (isset($_GET['input_image']) && $_GET['input_image'] == 0) echo '<em>No image uploaded!</em>'; ?>
    <?php if (isset($_GET['new_output']) && $_GET['new_output'] == 1) echo '<em>Image processed successfully!</em>'; ?>
    <?php if (isset($_GET['processed']) && $_GET['processed'] == 0) echo '<em>Image processing failed! Try again later.</em>'; ?>

    <form action="/upload.php" method="post" enctype="multipart/form-data">
        Upload an image
        <input type="file" name="input_image">
        <input type="submit" name="submit" value="Upload">
    </form>

    <hr>

    <?php
        require_once 'vendor/autoload.php';

        // $dotenv = Dotenv\Dotenv::create(__DIR__);
        // $dotenv->load();

        \Cloudinary::config(array(
            'cloud_name' => getenv('CLOUDINARY_CLOUD_NAME'), 
            'api_key' => getenv('CLOUDINARY_API_KEY'), 
            'api_secret' => getenv('CLOUDINARY_API_SECRET'),
        ));

        $redis = new Predis\Client(getenv('REDIS_URL'));

        $image_ids = $redis->lrange('image_ids', 0, -1);
        foreach ($image_ids as $image_id) {
            echo "<br>";
            echo "<div>";
            $image_objects = $redis->hgetall('image_objects_' . $image_id);
            foreach ($image_objects as $name => $frequency) {
                echo $name . ': ' . $frequency;
            }
            echo "</div>";

            $image_url = $redis->get('image_url_' . $image_id);
            echo "<a href=\"{$image_url}\" target=\"_blank\">";
            echo cl_image_tag($image_url, array(
                'height' => 200,
                'crop' => 'scale',
            ));
            echo "</a>";
            echo "<br>";
        }
    ?>
</body>
</html>