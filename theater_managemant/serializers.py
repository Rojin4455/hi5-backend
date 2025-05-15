from rest_framework import serializers
from .models import Theater, Screen, Tier, ScreenImage, Seat, SnackCategory, SnackItem, TheaterSnack
import cloudinary.uploader
from booking_management.models import Booking



class TheaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Theater
        fields = '__all__'



class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = '__all__'


class TierSerializer(serializers.ModelSerializer):

    seats = SeatSerializer(many=True, required=False)

    class Meta:
        model = Tier
        fields = ['name', 'price', 'total_seats', 'seats', 'id', 'rows', 'columns']

class ScreenImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScreenImage
        fields = ['image_url']


# class AllScreenSerializer(serializers.ModelSerializer):
#     screen_images = ScreenImageSerializer(many=True,read_only=True)
#     class Meta:
#         model = Screen
#         fields = ['name', 'type', 'tiers', 'screen_images', 'theater']



class ScreenSerializer(serializers.ModelSerializer):
    tiers = TierSerializer(many=True)
    screen_images = ScreenImageSerializer(many=True, required=False)
    

    class Meta:
        model = Screen
        order_by = '-id'
        fields = ['name', 'type', 'tiers', 'screen_images', 'theater', 'capacity','id']

    def create(self, validated_data):
        tiers_data = validated_data.pop('tiers')
        screen_images_data = validated_data.pop('screen_images', [])

        screen = Screen.objects.create(**validated_data)

        request = self.context.get('request')
        screen_images_data = request.FILES.getlist('screen_images[]')


        for image_file in screen_images_data:
            upload_result = cloudinary.uploader.upload(
                image_file,
                folder="screen_photos"
            )
            
            image_url = upload_result.get('secure_url')

            ScreenImage.objects.create(screen=screen, image_url=image_url)


        print("Screen images data: ", screen_images_data)
        
        i = 1
        for tier_data in tiers_data:
            print("tier_date", tier_data)
            Tier.objects.create(screen=screen, **tier_data, position = i)
            i += 1


        return screen

    def update(self, instance, validated_data):
        tiers_data = validated_data.pop('tiers', [])
        screen_images_data = validated_data.pop('screen_images', [])
        
        instance.name = validated_data.get('name', instance.name)
        instance.type = validated_data.get('type', instance.type)
        instance.capacity = validated_data.get('capacity', instance.capacity)
        instance.save()

        for tier_data in tiers_data:
            tier_id = tier_data.get('id', None)
            if tier_id:
                Tier.objects.filter(id=tier_id, screen=instance).update(**tier_data)
            else:
                Tier.objects.create(screen=instance, **tier_data)

        if screen_images_data:
            ScreenImage.objects.filter(screen=instance).delete()
            for image_data in screen_images_data:
                ScreenImage.objects.create(screen=instance, **image_data)

        return instance

    def validate(self, attrs):
        if 'tiers' not in attrs or not attrs['tiers']:
            raise serializers.ValidationError("At least one tier must be provided.")
        return attrs
    

class TheaterSnackCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SnackCategory
        fields = "__all__"
    
class SnackItemSerializerAll(serializers.ModelSerializer):
    category = TheaterSnackCategorySerializer()
    class Meta:
        model = SnackItem
        fields = "__all__"

class SnackCategorySerializer(serializers.ModelSerializer):
    snack_items = serializers.SerializerMethodField()
    class Meta:
        model = SnackCategory
        fields = "__all__"

    def get_snack_items(self, obj):
        available_snacks = self.context.get("available_snacks", None)
        if available_snacks is not None:
            snacks = obj.snack_items.filter(id__in=available_snacks)
        else:
            snacks = obj.snack_items.all()
        
        return SnackItemSerializerAll(snacks, many=True).data


class SnackItemSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(write_only=True)
    class Meta:
        model = SnackItem
        fields = ['name', 'description', 'is_vegetarian','image','calories', 'category', 'id']

    def create(self, validated_data):
        upload_result = cloudinary.uploader.upload(
            validated_data.pop("image"),
            folder="screen_photos"
        )
        
        image_url = upload_result.get('secure_url')

        validated_data['image_url'] = image_url

        return SnackItem.objects.create(**validated_data)



class TheaterSnackSerializer(serializers.ModelSerializer):
    theater_id = serializers.IntegerField(write_only=True)
    snack_id = serializers.IntegerField(write_only = True)
    snack_item = SnackItemSerializer(read_only=True)
    theater = TheaterSerializer(read_only=True)
    class Meta:
        model = TheaterSnack
        fields = ['theater_id', 'snack_id', 'price', 'stock', 'theater', 'snack_item']

    def create(self,validated_data):
        theater = Theater.objects.get(id=validated_data.pop('theater_id'))
        snack = SnackItem.objects.get(id=validated_data.pop('snack_id'))
        theater_snack = TheaterSnack.objects.create(
            theater=theater,
            snack_item=snack,
            is_available=True,
            **validated_data
        )

        return theater_snack
    
class TheaterFullSnacksSerializer(serializers.ModelSerializer):
    snack_item = SnackItemSerializerAll()

    class Meta:
        model = TheaterSnack
        fields = '__all__'
    


class BookingSerializer(serializers.ModelSerializer):
    total_bookings = serializers.FloatField()
    class Meta:
        model = Booking
        fields = [
                    'theater_name', 'screen_name', 'show_date', 'total_bookings'
                ]