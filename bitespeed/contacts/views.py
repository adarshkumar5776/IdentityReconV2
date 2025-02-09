from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Contact
from django.db.models import Q
from rest_framework import status


@api_view(["POST"])
def identify(request):
    """
    Identify and consolidate customer contact information based on email and phone number.
    """

    try:
        email = request.data.get("email")
        phone = request.data.get("phoneNumber")

        # Ensure at least one of email or phoneNumber is provided
        if not email and not phone:
            return Response(
                {"error": "At least one of email or phoneNumber is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Fetch all contacts that match the given email or phone number
        matching_contacts = Contact.objects.filter(Q(email=email) | Q(phoneNumber=phone))

        if matching_contacts.exists():
            # Retrieve all primary contacts from the matching results
            primary_contacts = list(matching_contacts.filter(linkPrecedence="primary"))

            # Determine the oldest primary contact
            primary_contact = min(primary_contacts, key=lambda c: c.createdAt)

            secondary_ids = []
            emails = set(matching_contacts.values_list("email", flat=True))
            phoneNumbers = set(matching_contacts.values_list("phoneNumber", flat=True))

            for contact in primary_contacts:
                if contact != primary_contact:
                    contact.linkPrecedence = "secondary"
                    contact.linkedId = primary_contact
                    contact.save()
                    secondary_ids.append(contact.id)

            # Fetch all secondary contacts linked to the primary contact
            secondary_contacts = Contact.objects.filter(linkedId=primary_contact)
            secondary_ids.extend(secondary_contacts.values_list("id", flat=True))

            # Create a new secondary contact if new information is provided
            if (email and email not in emails) or (phone and phone not in phoneNumbers):
                new_contact = Contact.objects.create(
                    email=email,
                    phoneNumber=phone,
                    linkedId=primary_contact,
                    linkPrecedence="secondary",
                )
                secondary_ids.append(new_contact.id)
                emails.add(email)
                phoneNumbers.add(phone)

        else:
            new_contact = Contact.objects.create(
                email=email, phoneNumber=phone, linkPrecedence="primary"
            )
            return Response(
                {
                    "contact": {
                        "primaryContactId": new_contact.id,
                        "emails": [email] if email else [],
                        "phoneNumbers": [phone] if phone else [],
                        "secondaryContactIds": [],
                    }
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "contact": {
                    "primaryContactId": primary_contact.id,
                    "emails": list(filter(None, emails)),
                    "phoneNumbers": list(filter(None, phoneNumbers)),
                    "secondaryContactIds": list(set(secondary_ids)),
                }
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        return Response(
            {"error": f"An unexpected error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
