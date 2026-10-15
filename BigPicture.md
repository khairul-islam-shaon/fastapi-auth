১. Client (Frontend/Postman) রিকোয়েস্ট পাঠায়
↓
২. [API Router] রিকোয়েস্ট গ্রহণ করে ও ডেটা ভ্যালিডেট করে (Pydantic Schema দিয়ে)
↓
৩. [Dependency Injection] ডাটাবেস সেশন ও সিকিউরিটি প্রোভাইড করে (`Depends`)
↓
৪. [Service Layer] বিজনেস লজিক এক্সিকিউট করে (পাসওয়ার্ড চেক, টোকেন বানানো)
↓
৫. [Repository Layer] ডেটাবেসে কুয়েরি চালায় (SELECT, INSERT ইত্যাদি)
↓
৬. [Database] PostgreSQL থেকে ডাটা রিটার্ন করে
