# thagomizer
For no particular reason in November of 2024 I started thinking about being able to communicate online in a secure manner and also to conceal the fact that the secure communication is happening. In my more paranoid moments I think about how the mere presence of encrypted message can look suspicious. Now a lot (most?) communication on the internet is ecnrypted by default with https connections, but it's probably relatively easy for State actors to break. So the idea is to conceal the fact that a file in transit is encrypted more by more than the default encryption. That's were thagomizer comes in.

Several years ago I remember reading about [steganography](https://en.wikipedia.org/wiki/Steganography) where information in hidden in something else that looks like something else. A simple example being putting each character of your message into the first character of each line of a different text. Another way is hide the binary version of your message in an image file. The data representing the image is just a series of numbers sepecifying the colors of each pixel. Lets say you have a file where each pixel is represented by 3 bytes, one byte each from red, blue, and green). For example you could have a a white pixel that is represented by (255, 255, 255) if you wanted to hide the number 4 (100 in binary) in that pixel you could change the values to (255, 254, 254) which is going to be almost white, but with just a tiny amount of red (assuming the byte order is RGB). The amount of red is almost certainly not detectable by the standard human eyeball. If we send the new version of the image file to someone who knows to look at this pixel and compose a number from the 3 least significant bits of the pixel RGB values they can discover we sent them 4.

Thagomizer does just that with input files that are a list of integers. It The first 16 bytes of color information encode the number of integers that are hidden in the file. So it can save up 65,536 distinct integers in an image. The next 24 bits encode the number of bits used to encode each number in the file. So it can represent integers up to 16,777,216.

The meat of thagomizer is in a class called Picture which can read in the image and input files, modify the image and save the modified image to a new file. It can also read in a file that has had the input inserted into it, extract the numbers and save them to a text file. It can also be used as a command-line tool like this:
 ```
 ./thagomizer -p <path_to_image_file> -i <path_to_input_file> -o <path_to_output_file> --insert
```
 or
```
./thagomizer.py -p <path_to_image_file> -o <path_to_output_file> --extract
```

Thagomizer uses opencv to read and write the image files. This means it has no problem inserting into and extracting out of png and tiff files. Jpegs are a problem since it's a lossy format and reading in a jpeg with opencv and immediately writing it back out results in a file with a different md5 sum. Inserted information is corrupted by the imwrite method.

But you're saying, wait why do I want to send numbers to someone in a sneaky manner, well if you go look at my cryptobook repo, you'll find a program that uses a long text file (eg, a book) as a source to encrypt a message you'd like to send to someone. The output of that program is a list of integers. So you can send those numbers to someone with thagomizer and they can turn those numbers back into the secret message if they know what book was used to encrypt it.