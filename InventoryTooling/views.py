from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView, DeleteView
from .models import ModelProduct, ModelLocation, ModelTempProdLoc, ModelTransaction
from django.urls import reverse, reverse_lazy
from django.db.models import Q, Sum, Count
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.forms import formset_factory, ModelForm

location = ModelLocation.objects.all()
temporary = ModelTempProdLoc.objects.all()
transaksi = ModelTransaction.objects.all()


# Templateview, UpdateView pakai get_context_data, listview pakai get_queryset
# Create your views here.

class MainMenu(TemplateView):
    template_name = 'main_menu.html'


# location
class ViewLocation(ListView):
    template_name = 'loc_list.html'

    # paginate_by = 6

    def get_queryset(self):
        object_list = location.filter(Q(status="FL") | Q(status="UL") | Q(status="HF") | Q(status="HU"))
        return object_list


class ResultLocation(ListView):
    template_name = 'loc_list.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        object_list = location.filter(
            Q(no_loc=query) | Q(assign=query) | Q(storage=query) | Q(status=query) | Q(area=query))
        if object_list:
            return object_list
        else:
            messages.add_message(self.request, messages.WARNING, "Location not found.")
            return False


class AddLocation(CreateView):
    template_name = 'loc_add.html'
    model = ModelLocation
    fields = ['no_loc', 'assign', 'storage', 'area']
    success_url = reverse_lazy('ViewLocation')

    def form_invalid(self, form):
        messages.add_message(self.request, messages.WARNING, "Location already exists.")
        return redirect('AddLocation')


class EditLocation(UpdateView):
    template_name = 'loc_edit.html'
    model = ModelLocation
    fields = ['assign', 'storage', 'status', 'area']
    context_object_name = 'data'
    success_url = reverse_lazy('ViewLocation')


class DeleteLocation(UpdateView):
    model = ModelLocation
    fields = ['status']
    success_url = reverse_lazy('ViewLocation')

    def form_valid(self, form):
        lok_fre = location.filter(no_loc=self.object.no_loc, status="FL")
        lok_ksg = location.filter(no_loc=self.object.no_loc, status="DL")
        if lok_fre:
            self.object = form.save()
            messages.add_message(self.request, messages.SUCCESS, "Location successfully deleted.")
        elif lok_ksg:
            self.object = form.save()
            messages.add_message(self.request, messages.SUCCESS, "Location successfully restored.")
        else:
            messages.add_message(self.request, messages.WARNING,
                                 "This action is available for free location status ")
        return HttpResponseRedirect(reverse('ViewLocation'))


# sampai sini ya view location

# product
class ViewProduct(ListView):
    template_name = 'prod_list.html'

    def get_queryset(self):
        object_list = ModelTempProdLoc.objects.all()
        return object_list


class DetailProduct(DetailView):
    template_name = 'prod_detail.html'
    model = ModelProduct
    context_object_name = 'data'


class ResultProduct(ListView):
    template_name = 'prod_list.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        object_list = temporary.filter(
            Q(prod_code_id=query) | Q(prod_code__prod_desc__icontains=query) | Q(no_loc_id=query) | Q(
                prod_code__status__icontains=query))
        if object_list:
            return object_list
        else:
            messages.add_message(self.request, messages.WARNING, "Product not found.")
            return False


class AddProduct(CreateView):
    template_name = 'prod_add.html'
    model = ModelProduct
    fields = ['prod_code', 'prod_desc', 'supplier', 'stock_min', 'stock_max', 'l_time_days']

    def form_invalid(self, form):
        messages.add_message(self.request, messages.WARNING, "No. Product already exists.")
        return redirect('AddProduct')

    def get_success_url(self, **kwargs):
        # beri value 'new' pada remark bahwa produk harus new line
        temporary.create(prod_code_id=self.object.prod_code, remark="NEW")
        messages.add_message(self.request, messages.SUCCESS, "Product added successfully.")
        return reverse('DetailProduct', kwargs={'pk': self.object.pk})


class EditProduct(UpdateView):
    template_name = 'prod_edit.html'
    model = ModelProduct
    fields = ['prod_desc', 'supplier', 'stock_min', 'stock_max', 'l_time_days', 'status']
    context_object_name = 'data'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # jika produk tidak memiliki lokasi bisa di inactive, begitupun sebaliknya
        context['object_list'] = temporary.filter(prod_code_id=self.object.pk, no_loc_id__isnull=True)
        return context

    def get_success_url(self, **kwargs):
        return reverse('DetailProduct', kwargs={'pk': self.object.pk})


# sampai sini ya view product


# Tambah lokasi untuk produk
class ViewNewline(ListView):
    template_name = 'newline_list.html'

    def get_queryset(self):
        object_list = temporary.filter(prod_code__status="ACTIVE").order_by('no_loc_id')
        return object_list


class ResultNewline(ListView):
    template_name = 'newline_list.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        object_list = temporary.filter(prod_code=query, prod_code__status="ACTIVE")
        if object_list:
            return object_list
        else:
            messages.add_message(self.request, messages.WARNING, "Product not found.")
            return False


class EditNewline(UpdateView):
    template_name = 'newline_add.html'
    model = ModelTempProdLoc
    fields = ['no_loc']
    context_object_name = 'data'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = location.filter(assign="P", status="FL")
        return context

    # jika lokasi belum terecord di database
    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, "Location not available.")
        return HttpResponseRedirect(reverse('EditNewline', kwargs={'pk': self.object.pk}))

    def form_valid(self, form):
        if temporary.filter(no_loc_id=self.object.no_loc_id).exists():
            # jika lokasi sudah digunakan produk lain
            messages.add_message(self.request, messages.WARNING, "Location is already in use.")
        elif location.filter(no_loc=self.object.no_loc_id).filter(Q(status="HU") | Q(status="HF") | Q(status="DL")):
            # jika status lokasi held / deleted
            messages.add_message(self.request, messages.ERROR, "Location is already in held or deleted.")
        else:
            self.object = form.save()
            # beri value 'LOC' pada remark bahwa produk sudah memiliki lokasi
            temporary.filter(no_loc_id=self.object.no_loc_id).update(remark="LOC")
            # beri value 'UL' bahwa status lokasi sudah digunakan
            location.filter(no_loc=self.object.no_loc_id).update(status="UL")
            messages.add_message(self.request, messages.SUCCESS, "Location has been successfully added to the product.")
        return HttpResponseRedirect(reverse('EditNewline', kwargs={'pk': self.object.pk}))


class DeleteNewline(UpdateView):
    template_name = 'newline_delete.html'
    model = ModelTempProdLoc
    fields = ['remark']
    context_object_name = 'data'

    def form_valid(self, form):
        qty_empty = temporary.filter(id=self.object.pk).filter(no_loc_id__status="UL", qty=0)
        if qty_empty:
            self.object = form.save()
            temporary.filter(id=self.object.pk).update(no_loc_id=None)
            location.filter(no_loc=self.object.no_loc_id).update(status="FL")
            messages.add_message(self.request, messages.SUCCESS, "Location has been deleted.")
        else:
            messages.add_message(self.request, messages.WARNING, "There is quantity or status held at this location.")
        return HttpResponseRedirect(reverse('EditNewline', kwargs={'pk': self.object.pk}))


# sampai sini ya view New Line


# proses-proses adjustment
class ViewRecordAdj(ListView):
    template_name = 'rec_adj_list.html'

    def get_queryset(self):
        object_list = transaksi.order_by('-date_created')
        return object_list


class ResultRecordAdj(ListView):
    template_name = 'rec_adj_list.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        object_list = transaksi.filter(Q(no_loc=query) | Q(prod_code=query))
        if object_list:
            return object_list
        else:
            messages.add_message(self.request, messages.WARNING, "Adjustment record not found.")
            return False


# TTB adjustment
class ViewReceiving(ListView):
    template_name = 'receive_list.html'

    def get_queryset(self):
        # object_list = transaksi.filter(no_ttb__isnull=False).order_by('-date_created')
        object_list = transaksi.filter(Q(ttb_stat="OR") | Q(ttb_stat="RE")).order_by('-date_created')
        # object_list = ModelTransaction.objects.filter(no_ttb__isnull=False).aggregate(prod_code=Sum("qty_adj"))["prod_code"]
        # object_list = ModelTransaction.objects.annotate(sum("qty_adj"))
        return object_list


class ResultReceiving(ListView):
    template_name = 'receive_list.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        object_list = transaksi.filter(Q(ttb_stat="OR") | Q(ttb_stat="RE"), no_ttb=query).order_by('-date_created')
        if object_list:
            return object_list
        else:
            messages.add_message(self.request, messages.WARNING, "No. TTB not found.")
            return False


class FormTransaction(ModelForm):
    class Meta:
        model = ModelTransaction
        fields = ['no_ttb', 'ttb_stat', 'ttb_qty', 'no_loc', 'trans_type', 'adj_type', 'prod_code', 'qty_bfr', 'qty_adj', 'qty_afr']


class AddReceiving(CreateView):
    # fungsi self.form_valid(...)  adalah save
    template_name = 'receive_add.html'
    model = ModelTransaction
    form_class = FormTransaction

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            # https://stackoverflow.com/questions/50313153/how-to-save-multiple-html-inputs-with-the-same-name-in-django
            a = request.POST.getlist('no_ttb')
            b = request.POST.getlist('prod_code')
            c = request.POST.getlist('qty')
            combine = min([len(a), len(b), len(c)])
            for i in range(combine):
                exist = transaksi.filter(no_ttb=a[i], prod_code=b[i]).exists()
                get = temporary.filter(prod_code_id=b[i])
                if exist:
                    # error jika sudah ada No TTB dengan product yang sudah terdaftar sebelumnya
                    messages.add_message(self.request, messages.ERROR,
                                         "No. TTB with product has been registered.")
                elif get.filter(remark="LOC"):
                    for e in get:
                        formset = self.form_class({
                            'no_ttb': a[i],
                            'ttb_stat': 'OR',  # remark sebagai ttb original belum di edit
                            'ttb_qty': c[i],
                            'no_loc': e.no_loc_id,
                            'trans_type': 'TTB',
                            'adj_type': 'AI',
                            'prod_code': b[i],
                            'qty_bfr': e.qty,
                            'qty_adj': c[i],
                            'qty_afr': int(e.qty) + int(c[i])
                        })
                        # check whether it's valid:
                        if formset.is_valid():
                            # update qty tb_temp
                            get.update(qty=int(e.qty) + int(c[i]))
                            formset.save()
                            # notif nya jadi banayak mengikuti jumlah input
                            messages.add_message(self.request, messages.SUCCESS, "No. TTB " + a[i] + " with product " + b[i] + " added successfully.")
                else:
                    messages.add_message(self.request, messages.ERROR, "Product " + b[i] + " location or product does "
                                                                                           "not exist.")
                    #return HttpResponseRedirect(reverse('AddReceiving'))
            return redirect('AddReceiving')


class UpdateReceiving(UpdateView):
    template_name = 'receive_update.html'
    model = ModelTransaction
    form_class = FormTransaction

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = transaksi.filter(id=self.object.pk)
        return context

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            id = self.request.POST.get('id')
            a = self.request.POST.get('no_ttb')
            b = self.request.POST.get('ttb_qty')  # qty ttb
            c = self.request.POST.get('prod_code')
            d = self.request.POST.get('qty')
            opsi = self.request.POST.get('adjust')
            # ambil qty dari status lokasi primary
            get = temporary.filter(prod_code_id=c, no_loc__assign="P")

            for e in get:
                if opsi == 'AO':  # adjust. out
                    # jika qty ttb. lebih kecil dari qty adjustment
                    if int(b) < int(d):
                        # error pengurangan jika nilai adj. lebih besar dari qty ttb
                        messages.add_message(self.request, messages.ERROR, "Avoid negative values.")
                        return HttpResponseRedirect(reverse('UpdateReceiving', kwargs={'pk': id}))
                    else:
                        formset = self.form_class({
                            'no_ttb': a,
                            'ttb_stat': 'RE',  # remark sebagai ttb revisi sudah di edit
                            'ttb_qty': int(b) - int(d),
                            'no_loc': e.no_loc_id,
                            'trans_type': 'TTB',
                            'adj_type': 'AO',
                            'prod_code': c,
                            'qty_bfr': e.qty,
                            'qty_adj': str("-") + str(int(d)),
                            'qty_afr': int(e.qty) - int(d)
                        })
                        # check whether it's valid:
                        if formset.is_valid():
                            # update qty tb_temp
                            get.update(qty=int(e.qty) - int(d))
                            # update ttb_stat NO menyatakan id ini sudah di edit
                            transaksi.filter(id=id).update(ttb_stat="NO")
                            formset.save()

                elif opsi == 'AI':  # adjust. in
                    formset = self.form_class(
                        {
                            'no_ttb': a,
                            'ttb_stat': 'RE',  # remark sebagai ttb revisi sudah di edit
                            'ttb_qty': int(b) + int(d),
                            'no_loc': e.no_loc_id,
                            'trans_type': 'TTB',
                            'adj_type': 'AI',
                            'prod_code': c,
                            'qty_bfr': e.qty,
                            'qty_adj': d,
                            'qty_afr': int(e.qty) + int(d),
                        })
                    # check whether it's valid:
                    if formset.is_valid():
                        # update qty tb_temp
                        get.update(qty=int(e.qty) + int(d))
                        # update ttb_stat NO menyatakan id ini sudah di edit
                        transaksi.filter(id=id).update(ttb_stat="NO")
                        formset.save()
                messages.add_message(self.request, messages.SUCCESS, "Stock has been successfully changed.")
                return HttpResponseRedirect(reverse('ViewReceiving'))

# sampai sini ya view receiving


# pick adjustment
class ViewPicking(ListView):
    template_name = 'pick_list.html'

    # filter by produk yang memiliki lokasi
    def get_queryset(self):
        object_list = temporary.filter(remark="LOC")
        return object_list


class ResultPicking(ListView):
    template_name = 'pick_list.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        # filter by produk yang memiliki lokasi
        object_list = temporary.filter(
            Q(prod_code_id=query) | Q(prod_code__prod_desc__icontains=query) | Q(no_loc_id=query) | Q(
                no_loc_id__storage=query) | Q(no_loc_id__area=query), remark="LOC")
        if object_list:
            return object_list
        else:
            messages.add_message(self.request, messages.WARNING, "Product not found.")
            return False


class UpdatePicking(UpdateView):
    template_name = 'pick_update.html'
    model = ModelTempProdLoc
    # fields = ['qty']
    form_class = FormTransaction
    context_object_name = 'data'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # filter by produk yang memiliki dengan transaksi tipe PCK
        context['object_list'] = transaksi.filter(no_loc=self.object.no_loc_id,
                                                  trans_type="PCK").order_by('-date_created')

        return context

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            id = self.request.POST.get('id')
            get = temporary.filter(id=id)
            adj_qty = self.request.POST.get('qty_adj')
            opsi = self.request.POST.get('adjust')
            for e in get:
                if opsi == 'AO':  # adjust. out
                    if int(adj_qty) > int(e.qty):
                        # error pengurangan jika nilai adj. lebih besar dari qty awal
                        messages.add_message(self.request, messages.ERROR, "Avoid negative values.")
                    else:
                        final = int(e.qty) - int(adj_qty)
                        # update qty tb_temp
                        get.update(qty=final)
                        # buat record di tb_transaction
                        transaksi.create(
                            no_loc=e.no_loc_id,
                            trans_type="PCK",
                            adj_type="AO",
                            prod_code=e.prod_code_id,
                            qty_bfr=int(e.qty),
                            qty_adj=str("-") + str(int(adj_qty)),
                            qty_afr=final,
                        )
                        messages.add_message(self.request, messages.SUCCESS, "Adjustment-out has been successfully.")
                elif opsi == 'AI':  # adjust. in
                    final = int(e.qty) + int(adj_qty)
                    # update qty tb_temp
                    get.update(qty=final)
                    # buat record di tb_transaction
                    transaksi.create(
                        no_loc=e.no_loc_id,
                        trans_type="PCK",
                        adj_type="AI",
                        prod_code=e.prod_code_id,
                        qty_bfr=int(e.qty),
                        qty_adj=int(adj_qty),
                        qty_afr=final,
                    )
                    messages.add_message(self.request, messages.SUCCESS, "Adjustment-in has been successfully.")
                return HttpResponseRedirect(reverse('UpdatePicking', kwargs={'pk': id}))


# sampai sini ya view picking

# stockopname adjustment
class ViewStockOpname(ListView):
    template_name = 'sto_list.html'
    model = ModelTempProdLoc

    # filter by lokasi yang memiliki status free lokasi dan used lokasi
    def get_queryset(self):
        object_list = location.filter(Q(status="FL") | Q(status="UL"))
        return object_list


class ResultStockOpname(ListView):
    template_name = 'sto_result.html'

    def get_queryset(self):
        query = self.request.GET.get('q')
        object_list = temporary.filter(no_loc_id=query)
        if object_list:
            return object_list
        else:
            messages.add_message(self.request, messages.WARNING, "Product not found.")
            return False


class UpdateStockOpname(UpdateView):
    model = ModelTempProdLoc
    fields = ['qty']
    success_url = reverse_lazy('ViewStockOpname')

    def get_success_url(self, **kwargs):
        # update status sto_check chk untuk lokasi sudah di sto
        location.filter(no_loc=self.object.no_loc_id).update(sto_check="CHK")
        messages.add_message(self.request, messages.SUCCESS, "Product added successfully.")
        # return reverse('DetailProduct', kwargs={'pk': self.object.pk})
        return reverse_lazy('ViewStockOpname')
