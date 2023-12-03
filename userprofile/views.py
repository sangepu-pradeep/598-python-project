from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, UpdateView, ListView

from accounts.models import User
from userprofile.models import Profile

import pandas as pd # For data processing
import numpy as np # For linear algebra
import matplotlib.pyplot as plt # For plotting


class TimelineView(DetailView):
    model = User
    template_name = "profile/user-profile.html"
    slug_field = "username"
    slug_url_kwarg = "username"
    context_object_name = "user"
    object = None

    def get_object(self, queryset=None):
        return self.model.objects.select_related('profile').prefetch_related("posts").get(username=self.kwargs.get(self.slug_url_kwarg))

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class ProfileEditView(UpdateView):
    model = Profile
    template_name = "profile/edit-my-profile.html"
    context_object_name = "profile"
    object = None
    fields = "__all__"

    def get_object(self, queryset=None):
        return self.request.user.profile

    def post(self, request, *args, **kwargs):
        print(request.POST.get('first_name'))
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.about = request.POST.get('about')
        if request.POST.get('gender') == "male":
            user.gender = "male"
        else:
            user.gender = "female"
        user.save()
        profile = user.profile
        profile.country = request.POST.get('country')
        profile.city = request.POST.get('city')
        profile.phone = request.POST.get('phone')
        profile.save()
        return redirect(reverse_lazy('profile:edit-profile'))

class Profileusersinfo(DetailView):
    model = Profile
    template_name = "profile/user-info.html"
    context_object_name = "profile"
    object = None
    fields = "__all__"

    def get_object(self):
        current_user_friends = pd.read_csv("row_data.csv")
        print("satvik")
        print(current_user_friends.head())
        data = pd.DataFrame(current_user_friends, columns=['ID','q11'])
        res=[]
        for i in data['q11']:
            res.append(i)
        fig, ax = plt.subplots(figsize=(12, 2), subplot_kw=dict(aspect="equal"), dpi= 80)
        labels2 = ['Male', 'Female']
        sizes2 = [res.count("male"), res.count("female")]
        plt.pie(sizes2, labels=labels2, autopct='%.0f%%')
        plt.savefig("gender-Python.png", bbox_inches='tight', dpi=300)

        return "gender-Python.png"
