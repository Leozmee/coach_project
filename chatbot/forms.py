from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import User, UserProfile, WorkoutProgram, RAGDocument, FewShotExample

class CustomUserCreationForm(UserCreationForm):
    """Formulaire d'inscription personnalisé"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'votre@email.com'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Prénom'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nom'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom d\'utilisateur'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmer le mot de passe'
        })
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Créer automatiquement le profil
            UserProfile.objects.create(user=user)
        return user

class CustomLoginForm(AuthenticationForm):
    """Formulaire de connexion personnalisé"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email ou nom d\'utilisateur'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mot de passe'
        })
    )

class UserProfileForm(forms.ModelForm):
    """Formulaire de profil utilisateur"""
    
    class Meta:
        model = UserProfile
        fields = [
            'age', 'gender', 'height', 'weight',
            'fitness_level', 'primary_goal',
            'limitations', 'equipment_available'
        ]
        widgets = {
            'age': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Âge en années'
            }),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Taille en cm'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Poids en kg',
                'step': '0.1'
            }),
            'fitness_level': forms.Select(attrs={'class': 'form-select'}),
            'primary_goal': forms.Select(attrs={'class': 'form-select'}),
            'limitations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Blessures, limitations physiques, allergies...'
            }),
            'equipment_available': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Haltères, tapis, élastiques, machine...'
            }),
        }

class WorkoutProgramForm(forms.ModelForm):
    """Formulaire de programme d'entraînement"""
    
    class Meta:
        model = WorkoutProgram
        fields = ['title', 'description', 'difficulty', 'duration_weeks', 'sessions_per_week', 'is_favorite']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du programme'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description du programme...'
            }),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'duration_weeks': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 52
            }),
            'sessions_per_week': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 7
            }),
            'is_favorite': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class RAGDocumentForm(forms.ModelForm):
    """Formulaire pour ajouter/modifier des documents RAG"""
    
    class Meta:
        model = RAGDocument
        fields = ['title', 'content', 'category', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Titre du document'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Contenu détaillé du document...'
            }),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class FewShotExampleForm(forms.ModelForm):
    """Formulaire pour ajouter des exemples de conversation"""
    
    class Meta:
        model = FewShotExample
        fields = ['question', 'answer', 'context', 'is_active']
        widgets = {
            'question': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Question type de l\'utilisateur'
            }),
            'answer': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Réponse modèle attendue'
            }),
            'context': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BulkRAGUploadForm(forms.Form):
    """Formulaire pour upload en masse de documents RAG"""
    file = forms.FileField(
        label="Fichier CSV/TXT",
        help_text="Format: titre,contenu,catégorie (une ligne par document)",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.txt'
        })
    )
    category = forms.ChoiceField(
        choices=RAGDocument.CATEGORY_CHOICES,
        initial='general',
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Catégorie par défaut si non spécifiée dans le fichier"
    )