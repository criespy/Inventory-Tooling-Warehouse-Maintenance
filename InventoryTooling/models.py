from django.db import models
from django.utils import timezone


# Class NameField create upper string
class NameField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(NameField, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        return str(value).upper()


# Create your models here
class ModelProduct(models.Model):
    prod_code = NameField(max_length=20, primary_key=True)
    prod_desc = NameField(max_length=60, null=True)
    supplier = NameField(max_length=60, null=True)
    stock_min = models.IntegerField(null=True)
    stock_max = models.IntegerField(null=True)
    # no_loc = NameField(max_length=20, null=True)
    l_time_days = models.IntegerField(null=True)
    status = NameField(default='ACTIVE', max_length=60, null=True)

    class Meta:
        db_table = "tb_Product"


class ModelLocation(models.Model):
    no_loc = NameField(max_length=20, primary_key=True)
    assign = models.CharField(max_length=1, null=True)
    storage = NameField(max_length=2, null=True)
    area = NameField(max_length=2, null=True)
    status = models.CharField(default='FL', max_length=2, null=True)
    sto_check = models.CharField(max_length=3, null=True)

    class Meta:
        db_table = "tb_Location"


# Create your models here
class ModelTempProdLoc(models.Model):
    prod_code = models.ForeignKey(ModelProduct, on_delete=models.CASCADE, null=True)
    no_loc = models.ForeignKey(ModelLocation, on_delete=models.CASCADE, null=True)
    remark = NameField(max_length=3, null=True)  # untuk remark pada proses yang berkaitan
    qty = models.IntegerField(default=0, null=True)

    class Meta:
        db_table = "tb_TempProdLoc"


class ModelTransaction(models.Model):
    no_ttb = models.CharField(max_length=10, null=True)
    ttb_stat = models.CharField(max_length=2, null=True)
    ttb_qty = models.IntegerField(null=True)  # qty ttb
    no_loc = NameField(max_length=20, null=True)
    trans_type = models.CharField(max_length=3, null=True)
    adj_type = models.CharField(max_length=2, null=True)
    prod_code = NameField(max_length=20, null=True)
    qty_bfr = models.IntegerField(null=True)  # qty before
    qty_adj = models.IntegerField(null=True)  # qty yang di adjustment
    qty_afr = models.IntegerField(null=True)  # qty after
    date_created = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        db_table = "tb_transaction"
