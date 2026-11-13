import { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight, Baby, Bell, BookOpen, CalendarDays, Check, CheckCircle2, ChevronDown,
  ChevronRight, CircleHelp, Clock3, ExternalLink, Heart, Home, Info, Leaf, MapPin,
  Menu, MessageCircle, Navigation, NotebookPen, Phone, PhoneCall, Play, Plus, Send,
  ShieldCheck, ShoppingBag, Sparkles, Stethoscope, Sun, Video, WalletCards, Wind, X,
} from 'lucide-react';

type PayPalOrderActions = {
  order: {
    create: (order: { purchase_units: Array<{ description: string; amount: { value: string; currency_code: string } }> }) => Promise<string>;
    capture: () => Promise<{ payer?: { name?: { given_name?: string } } }>;
  };
};

type PayPalButtonsInstance = {
  render: (container: string) => Promise<void>;
  close?: () => Promise<void>;
};

declare global {
  interface Window {
    paypal?: {
      Buttons: (options: {
        createOrder: (_data: unknown, actions: PayPalOrderActions) => Promise<string>;
        onApprove: (_data: unknown, actions: PayPalOrderActions) => Promise<void>;
        onError?: (error: unknown) => void;
      }) => PayPalButtonsInstance;
    };
  }
}

type Tab = 'Today' | 'Learn' | 'Journal' | 'Care team' | 'Explore' | 'Sessions';
const WHATSAPP = '94777959386';
const whatsapp = (text: string) => `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(text)}`;
const maps = (query: string) => `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
const moods = [{ label: 'Peaceful', emoji: '☺', color: '#b8e4d3' }, { label: 'Okay', emoji: '•ᴗ•', color: '#dce8c0' }, { label: 'Tired', emoji: '◡︵◡', color: '#f5dfb7' }, { label: 'Anxious', emoji: '◕︵◕', color: '#f3c5c0' }];
const symptoms = ['Nausea', 'Headache', 'Back ache', 'Swelling', 'Breathless', 'None today'];
const lessons = [
  { id: 'movement', category: 'Your body', title: 'Understanding baby movement', time: '4 min read', icon: Baby, color: 'bg-[#eaf6ef] text-[#5e9882]', summary: 'Learn what movement patterns can feel like in the third trimester and when to pause and check in.', points: ['Every baby has a different rhythm.', 'Notice your baby’s usual pattern, not a perfect number.', 'Contact your maternity team if movement feels reduced or different.'] },
  { id: 'nutrition', category: 'Nutrition', title: 'Building a nourishing plate', time: '5 min read', icon: ShoppingBag, color: 'bg-[#fff4df] text-[#c28a4b]', summary: 'A practical guide to hydration, iron-rich foods, protein, and the questions worth asking about supplements.', points: ['Aim for variety across the day.', 'Ask your clinician before starting or changing supplements.', 'Keep fluids nearby and notice what your body tolerates.'] },
  { id: 'rest', category: 'Wellbeing', title: 'Why rest is real care', time: '3 min read', icon: Heart, color: 'bg-[#fff1ec] text-[#df7967]', summary: 'Rest supports your changing body, your nervous system, and the energy you need for birth and recovery.', points: ['Short pauses count as rest.', 'Ask for practical support before you feel depleted.', 'Gentle movement and comfortable positions can help.'] },
  { id: 'appointments', category: 'Prepare', title: 'Make appointments work for you', time: '5 min read', icon: NotebookPen, color: 'bg-[#eef6f7] text-[#5d9c9b]', summary: 'A simple way to bring questions, symptoms, and preferences into your next care conversation.', points: ['Write down changes since your last visit.', 'Bring your questions, even if they feel small.', 'Ask who to contact between appointments.'] },
];
const places = [
  { type: 'Maternity hospital', name: 'Your nearest maternity unit', detail: 'Find emergency and scheduled maternity care', icon: Stethoscope, query: 'maternity hospital near me', color: 'bg-[#fff0eb] text-[#df7967]' },
  { type: 'Women’s clinic', name: 'Women’s health clinic', detail: 'Appointments, midwife support, and check-ins', icon: Heart, query: 'women health clinic near me', color: 'bg-[#eaf6ef] text-[#5e9882]' },
  { type: 'Nutrition shop', name: 'Pregnancy nutrition delivery', detail: 'Find local supplement and grocery delivery', icon: ShoppingBag, query: 'prenatal vitamins nutrition shop near me', color: 'bg-[#fff4df] text-[#c28a4b]' },
];

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('Today');
  const [mood, setMood] = useState('');
  const [selectedSymptoms, setSelectedSymptoms] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);
  const [breathing, setBreathing] = useState(false);
  const [breathCount, setBreathCount] = useState(4);
  const [menu, setMenu] = useState(false);
  const [notifications, setNotifications] = useState(false);
  const [urgent, setUrgent] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [completed, setCompleted] = useState<string[]>([]);
  const [journal, setJournal] = useState('');
  const [savedJournal, setSavedJournal] = useState('');
  const [message, setMessage] = useState('');
  const [sentMessage, setSentMessage] = useState('');
  const [booking, setBooking] = useState(false);
  const [bookingDate, setBookingDate] = useState('2026-11-12');
  const [bookingTime, setBookingTime] = useState('10:00');
  const [bookingType, setBookingType] = useState('Midwife check-in');
  const [bookingSent, setBookingSent] = useState(false);

  useEffect(() => {
    if (!breathing) return;
    const timer = window.setInterval(() => setBreathCount((v) => v === 4 ? 1 : v + 1), 1000);
    return () => window.clearInterval(timer);
  }, [breathing]);

  const navigate = (tab: Tab) => { setActiveTab(tab); setMenu(false); window.scrollTo({ top: 0, behavior: 'smooth' }); };
  const toggleSymptom = (symptom: string) => {
    setSelectedSymptoms((current) => current.includes(symptom) ? current.filter((x) => x !== symptom) : symptom === 'None today' ? ['None today'] : [...current.filter((x) => x !== 'None today'), symptom]);
    setSaved(false);
  };
  const todayLabel = useMemo(() => new Intl.DateTimeFormat('en', { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date()), []);

  return <div className="min-h-screen bg-[#fffaf6] text-[#24363a]">
    <header className="sticky top-0 z-30 border-b border-[#efe5de] bg-[#fffaf6]/95 backdrop-blur"><div className="mx-auto flex max-w-[1180px] items-center justify-between px-5 py-4 sm:px-8 lg:px-10">
      <button onClick={() => navigate('Today')} className="flex items-center gap-3 text-left"><div className="grid h-10 w-10 place-items-center rounded-[15px] bg-[#2f6260] text-white shadow-[0_8px_20px_rgba(47,98,96,.18)]"><Leaf size={19} /></div><div><p className="text-[17px] font-bold tracking-[-.04em]">Placenta<span className="text-[#df7967]">Sync</span></p><p className="text-[9px] font-bold uppercase tracking-[.19em] text-[#a2a9a4]">Your gentle care loop</p></div></button>
      <nav className="hidden max-w-[610px] items-center gap-1 overflow-x-auto rounded-full border border-[#eee4dc] bg-white p-1 lg:flex">{(['Today', 'Learn', 'Explore', 'Sessions', 'Journal', 'Care team'] as Tab[]).map((tab) => <button key={tab} onClick={() => navigate(tab)} className={`whitespace-nowrap rounded-full px-3 py-2 text-[10px] font-bold transition ${activeTab === tab ? 'bg-[#2f6260] text-white' : 'text-[#7b8985] hover:bg-[#f8f2ed]'}`}>{tab === 'Learn' && <BookOpen size={12} className="mr-1 inline" />}{tab === 'Explore' && <MapPin size={12} className="mr-1 inline" />}{tab === 'Sessions' && <CalendarDays size={12} className="mr-1 inline" />}{tab === 'Journal' && <NotebookPen size={12} className="mr-1 inline" />}{tab === 'Care team' && <MessageCircle size={12} className="mr-1 inline" />}{tab}</button>)}</nav>
      <div className="relative flex items-center gap-2"><button onClick={() => setNotifications(!notifications)} className="relative grid h-9 w-9 place-items-center rounded-full border border-[#eee4dc] text-[#758581]"><Bell size={16} /><span className="absolute right-2 top-1.5 h-1.5 w-1.5 rounded-full bg-[#df7967]" /></button><button className="hidden items-center gap-2 rounded-full bg-[#f7efe9] px-3 py-2 text-[11px] font-bold text-[#866c61] sm:flex"><Sun size={14} className="text-[#e7a65a]" /> 28 weeks</button><button onClick={() => setMenu(!menu)} className="grid h-9 w-9 place-items-center rounded-full border border-[#eee4dc] text-[#758581] lg:hidden">{menu ? <X size={17} /> : <Menu size={17} />}</button><div className="hidden h-9 w-9 place-items-center rounded-full bg-[#f2cfc3] text-[10px] font-bold text-[#8c5c52] sm:grid">AM</div>{notifications && <div className="absolute right-0 top-12 z-40 w-72 rounded-2xl border border-[#efe5de] bg-white p-4 text-left shadow-xl"><div className="flex items-center justify-between"><p className="text-xs font-bold">Your notifications</p><button onClick={() => setNotifications(false)}><X size={14} /></button></div><p className="mt-3 rounded-xl bg-[#eff8f4] p-3 text-[11px] leading-relaxed text-[#4c756b]"><b>All clear.</b> Your care team has no new requests today.</p></div>}</div>
    </div>{menu && <div className="mx-5 mb-4 rounded-2xl border border-[#efe5de] bg-white p-2 shadow-lg lg:hidden">{(['Today', 'Learn', 'Explore', 'Sessions', 'Journal', 'Care team'] as Tab[]).map((tab) => <button key={tab} onClick={() => navigate(tab)} className={`flex w-full items-center gap-3 rounded-xl p-3 text-left text-xs font-bold ${activeTab === tab ? 'bg-[#eff8f4] text-[#34716d]' : 'text-[#71807b]'}`}>{tab === 'Today' ? <Home size={16} /> : tab === 'Learn' ? <BookOpen size={16} /> : tab === 'Explore' ? <MapPin size={16} /> : tab === 'Sessions' ? <CalendarDays size={16} /> : tab === 'Journal' ? <NotebookPen size={16} /> : <MessageCircle size={16} />}{tab}</button>)}</div>}</header>
    <main className="mx-auto max-w-[1180px] px-5 pb-10 sm:px-8 lg:px-10">
      {activeTab === 'Today' && <Today {...{ mood, setMood, selectedSymptoms, toggleSymptom, saved, setSaved, breathing, setBreathing, breathCount, setBreathCount, navigate, setUrgent, todayLabel }} />}
      {activeTab === 'Learn' && <Learn expanded={expanded} setExpanded={setExpanded} completed={completed} setCompleted={setCompleted} />}
      {activeTab === 'Explore' && <Explore setUrgent={setUrgent} />}
      {activeTab === 'Sessions' && <Sessions {...{ booking, setBooking, bookingDate, setBookingDate, bookingTime, setBookingTime, bookingType, setBookingType, bookingSent, setBookingSent }} />}
      {activeTab === 'Journal' && <Journal {...{ journal, setJournal, savedJournal, setSavedJournal }} />}
      {activeTab === 'Care team' && <CareTeam {...{ message, setMessage, sentMessage, setSentMessage }} />}
    </main>
    {urgent && <div className="fixed inset-0 z-50 grid place-items-center bg-[#24363a]/35 p-5"><div className="w-full max-w-md rounded-[26px] bg-white p-6 shadow-2xl"><div className="flex items-start justify-between"><div className="grid h-10 w-10 place-items-center rounded-xl bg-[#fff0eb] text-[#df7967]"><PhoneCall size={19} /></div><button onClick={() => setUrgent(false)}><X size={18} /></button></div><h2 className="mt-5 text-xl font-bold">You know your body best.</h2><p className="mt-2 text-sm leading-relaxed text-[#71807b]">If something feels urgent, contact your maternity team or local emergency services now. PlacentaSync cannot assess emergencies.</p><div className="mt-5 space-y-2"><a href={`tel:+${WHATSAPP}`} className="flex w-full items-center justify-center gap-2 rounded-xl bg-[#df7967] py-3 text-xs font-bold text-white">Call care support <Phone size={14} /></a><button onClick={() => setUrgent(false)} className="w-full rounded-xl border border-[#eee5de] py-3 text-xs font-bold text-[#71807b]">Close</button></div></div></div>}
  </div>;
}

function Today({ mood, setMood, selectedSymptoms, toggleSymptom, saved, setSaved, breathing, setBreathing, breathCount, setBreathCount, navigate, setUrgent, todayLabel }: any) {
  return <><section className="relative mt-3 overflow-hidden rounded-[30px] bg-[#e7f2eb] px-6 py-8 sm:px-10 sm:py-10"><div className="absolute -right-10 -top-20 h-64 w-64 rounded-full border-[34px] border-[#d1e8dc]" /><div className="relative max-w-[680px]"><div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.2em] text-[#548b78]"><Sparkles size={14} /> {todayLabel}</div><h1 className="mt-4 text-[31px] font-bold leading-[1.08] tracking-[-.06em] text-[#25494a] sm:text-[43px]">A softer way to<br /><span className="text-[#df7967]">check in with you.</span></h1><p className="mt-4 max-w-[510px] text-[13px] leading-relaxed text-[#5b7772]">Your body is doing extraordinary work. Take one quiet minute to notice what you need today.</p><button onClick={() => document.getElementById('check-in')?.scrollIntoView({ behavior: 'smooth' })} className="mt-6 flex items-center gap-2 rounded-xl bg-[#2f6260] px-4 py-3 text-xs font-bold text-white">Start today’s check-in <ArrowRight size={15} /></button></div></section>
    <div className="mt-7 grid grid-cols-1 gap-5 lg:grid-cols-[1.25fr_.75fr]"><section id="check-in" className="rounded-[24px] border border-[#eee5de] bg-white p-5 shadow-sm sm:p-7"><div className="flex items-start justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.2em] text-[#a4aaa4]">Daily check-in · 1 of 3</p><h2 className="mt-2 text-[21px] font-bold tracking-[-.04em]">How are you feeling right now?</h2></div><Heart size={20} className="text-[#df7967]" /></div><div className="mt-6 grid grid-cols-2 gap-2 sm:grid-cols-4">{moods.map((item) => <button key={item.label} onClick={() => { setMood(item.label); setSaved(false); }} className={`rounded-2xl border p-3 text-center ${mood === item.label ? 'border-[#4f9684] bg-[#eff8f4]' : 'border-[#f0e7e0]'}`}><span className="mx-auto grid h-11 w-11 place-items-center rounded-full text-[19px]" style={{ backgroundColor: item.color }}>{item.emoji}</span><span className="mt-2 block text-[11px] font-bold text-[#687874]">{item.label}</span></button>)}</div><div className="mt-7 border-t border-[#f2ebe5] pt-6"><p className="text-[13px] font-bold">Anything your body is telling you?</p><p className="mt-1 text-[11px] text-[#9aa39f]">Select all that feel relevant. There is no right answer.</p><div className="mt-4 flex flex-wrap gap-2">{symptoms.map((s) => <button key={s} onClick={() => toggleSymptom(s)} className={`rounded-full border px-3 py-2 text-[11px] font-semibold ${selectedSymptoms.includes(s) ? 'border-[#7eb6a1] bg-[#eaf6ef] text-[#397866]' : 'border-[#eee5de] text-[#7b8985]'}`}>{selectedSymptoms.includes(s) && <Check size={12} className="mr-1 inline" />}{s}</button>)}</div></div><button disabled={!mood} onClick={() => setSaved(true)} className="mt-7 flex w-full items-center justify-center gap-2 rounded-xl bg-[#df7967] py-3 text-xs font-bold text-white disabled:opacity-40">{saved ? <><Check size={15} /> Saved for today</> : <>Save my check-in <ArrowRight size={15} /></>}</button></section>
      <div className="space-y-5"><section className="rounded-[24px] bg-[#2f6260] p-6 text-white"><div className="flex items-start justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.2em] text-[#a9d8c5]">A moment to settle</p><h2 className="mt-2 text-[22px] font-bold">Breathe with baby</h2></div><Wind size={23} className="text-[#a9d8c5]" /></div><p className="mt-3 text-[12px] leading-relaxed text-[#c5ded5]">A simple 60-second rhythm to soften your shoulders.</p><div className="mt-6 flex items-center gap-4"><div className={`grid h-20 w-20 place-items-center rounded-full border-2 border-[#91cdb9] ${breathing ? 'animate-pulse bg-[#4b8078]' : 'bg-[#3a716d]'}`}><span className="text-[11px] font-bold">{breathing ? `${breathCount}s` : '1 min'}</span></div><button onClick={() => { setBreathing(!breathing); setBreathCount(4); }} className="rounded-xl bg-white px-4 py-2.5 text-[11px] font-bold text-[#2f6260]">{breathing ? 'Pause' : 'Begin'}</button></div></section><section className="rounded-[24px] border border-[#eee5de] bg-white p-6"><div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-[#fff2eb] text-[#df7967]"><Baby size={19} /></div><div><h3 className="text-[14px] font-bold">Baby’s little note</h3><p className="text-[10px] text-[#99a39f]">A gentle reminder for today</p></div></div><p className="mt-5 text-[15px] font-semibold leading-relaxed text-[#405452]">“Your rest is productive too. You don’t have to earn a pause.”</p><button onClick={() => navigate('Learn')} className="mt-5 flex items-center gap-2 text-[10px] font-bold text-[#5e9882]">Explore week 28 learning <ArrowRight size={12} /></button></section></div></div>
    <section className="mt-5 grid grid-cols-1 gap-5 md:grid-cols-3"><button onClick={() => navigate('Explore')} className="rounded-[22px] border border-[#eee5de] bg-white p-5 text-left"><MapPin size={19} className="text-[#5e9882]" /><h3 className="mt-4 text-[14px] font-bold">Find nearby care</h3><p className="mt-1 text-[11px] text-[#8c9994]">Clinics, hospitals, shops, and delivery.</p></button><button onClick={() => navigate('Sessions')} className="rounded-[22px] border border-[#eee5de] bg-white p-5 text-left"><CalendarDays size={19} className="text-[#5d9c9b]" /><h3 className="mt-4 text-[14px] font-bold">Book a session</h3><p className="mt-1 text-[11px] text-[#8c9994]">Choose a time with your care team.</p></button><button onClick={() => setUrgent(true)} className="rounded-[22px] border border-[#f4d9d2] bg-[#fff8f4] p-5 text-left"><PhoneCall size={19} className="text-[#df7967]" /><h3 className="mt-4 text-[14px] font-bold text-[#704f4a]">Need urgent help?</h3><p className="mt-1 text-[11px] text-[#98746d]">Trust yourself and contact care.</p></button></section><Safety /></>;
}

function Learn({ expanded, setExpanded, completed, setCompleted }: any) {
  const complete = (id: string) => setCompleted(completed.includes(id) ? completed.filter((x: string) => x !== id) : [...completed, id]);
  return <><section className="mt-3 rounded-[30px] bg-[#e7f2eb] px-6 py-8 sm:px-10 sm:py-10"><p className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.2em] text-[#548b78]"><BookOpen size={14} /> Maternal education · week 28</p><h1 className="mt-4 text-[31px] font-bold leading-tight tracking-[-.06em] text-[#25494a] sm:text-[43px]">Knowledge that makes<br /><span className="text-[#df7967]">care conversations easier.</span></h1><p className="mt-4 max-w-[570px] text-[13px] leading-relaxed text-[#5b7772]">Short, kind explainers to help you notice patterns, prepare questions, and feel more confident speaking with your care team.</p></section><div className="mt-7 flex items-end justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.2em] text-[#a4aaa4]">Your learning shelf</p><h2 className="mt-2 text-2xl font-bold">Start where you are</h2></div><span className="rounded-full bg-[#eaf6ef] px-3 py-2 text-[10px] font-bold text-[#5e9882]">{completed.length}/4 complete</span></div><div className="mt-4 space-y-3">{lessons.map((lesson) => { const Icon = lesson.icon; const open = expanded === lesson.id; const done = completed.includes(lesson.id); return <article key={lesson.id} className="rounded-[22px] border border-[#eee5de] bg-white p-5"><button onClick={() => setExpanded(open ? null : lesson.id)} className="flex w-full items-center gap-4 text-left"><div className={`grid h-11 w-11 shrink-0 place-items-center rounded-2xl ${lesson.color}`}><Icon size={20} /></div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><span className="text-[9px] font-bold uppercase tracking-[.15em] text-[#a4aaa4]">{lesson.category}</span>{done && <span className="rounded-full bg-[#eaf6ef] px-2 py-1 text-[9px] font-bold text-[#5e9882]">Complete</span>}</div><h3 className="mt-1 text-[15px] font-bold">{lesson.title}</h3><p className="mt-1 text-[11px] text-[#8c9994]">{lesson.time}</p></div>{open ? <ChevronDown size={18} /> : <ChevronRight size={18} />}</button>{open && <div className="mt-5 border-t border-[#f2ebe5] pt-5"><p className="text-[13px] leading-relaxed text-[#5f716d]">{lesson.summary}</p><ul className="mt-4 space-y-2">{lesson.points.map((point) => <li key={point} className="flex gap-2 text-[11px] text-[#71807b]"><CheckCircle2 size={15} className="shrink-0 text-[#6daf91]" />{point}</li>)}</ul><button onClick={() => complete(lesson.id)} className={`mt-5 flex items-center gap-2 rounded-xl px-4 py-2.5 text-[11px] font-bold ${done ? 'bg-[#eaf6ef] text-[#5e9882]' : 'bg-[#2f6260] text-white'}`}>{done ? <><Check size={14} /> Marked as complete</> : <>Mark as learned <Check size={14} /></>}</button></div>}</article>; })}</div><Safety /></>;
}

function Explore({ setUrgent }: { setUrgent: (value: boolean) => void }) {
  const [location, setLocation] = useState(false);
  return <><section className="mt-3 rounded-[30px] bg-[#eef6f7] px-6 py-8 sm:px-10 sm:py-10"><p className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.2em] text-[#5d9c9b]"><MapPin size={14} /> Care access map</p><h1 className="mt-4 text-[31px] font-bold leading-tight tracking-[-.06em] text-[#315b5e] sm:text-[43px]">Care is more than<br /><span className="text-[#df7967]">one appointment.</span></h1><p className="mt-4 max-w-[580px] text-[13px] leading-relaxed text-[#668486]">Find nearby support, then choose the kind of help that fits this moment.</p><button onClick={() => setLocation(true)} className="mt-6 flex items-center gap-2 rounded-xl bg-[#2f6260] px-4 py-3 text-xs font-bold text-white"><Navigation size={14} /> {location ? 'Location enabled' : 'Use my location'}</button></section><div className="mt-7 grid grid-cols-1 gap-4 md:grid-cols-3">{places.map((place) => { const Icon = place.icon; return <article key={place.type} className="rounded-[22px] border border-[#eee5de] bg-white p-5"><div className={`grid h-11 w-11 place-items-center rounded-2xl ${place.color}`}><Icon size={20} /></div><p className="mt-5 text-[9px] font-bold uppercase tracking-[.16em] text-[#a4aaa4]">{place.type}</p><h2 className="mt-2 text-[15px] font-bold">{place.name}</h2><p className="mt-2 text-[11px] leading-relaxed text-[#8c9994]">{place.detail}</p><div className="mt-5 flex gap-2"><a href={maps(place.query)} target="_blank" rel="noreferrer" className="flex flex-1 items-center justify-center gap-1 rounded-xl bg-[#eff8f4] py-2.5 text-[10px] font-bold text-[#397866]"><MapPin size={13} /> Map</a><a href={whatsapp(`Hi PlacentaSync, I need help finding ${place.type.toLowerCase()} support.`)} target="_blank" rel="noreferrer" className="grid w-10 place-items-center rounded-xl bg-[#eaf6ef] text-[#397866]"><MessageCircle size={14} /></a></div></article>; })}</div><section className="mt-5 rounded-[22px] border border-[#f4d9d2] bg-[#fff8f4] p-5"><div className="flex gap-3"><ShoppingBag size={19} className="shrink-0 text-[#df7967]" /><div><h2 className="text-[14px] font-bold text-[#704f4a]">Nutrition delivery shortcuts</h2><p className="mt-1 text-[11px] leading-relaxed text-[#98746d]">Search local supplement shops and delivery options. Always check new supplements with your clinician first.</p><div className="mt-4 flex flex-wrap gap-2"><a href={maps('prenatal vitamins delivery near me')} target="_blank" rel="noreferrer" className="rounded-xl bg-white px-3 py-2 text-[10px] font-bold text-[#c76456]">Find supplements <ExternalLink size={12} className="ml-1 inline" /></a><a href={maps('healthy food delivery near me')} target="_blank" rel="noreferrer" className="rounded-xl bg-white px-3 py-2 text-[10px] font-bold text-[#c76456]">Find food delivery <ExternalLink size={12} className="ml-1 inline" /></a></div></div></div></section><Safety /></>;
}

function PayPalCheckout({ amount, description, onSuccess }: { amount: string; description: string; onSuccess: (name: string) => void }) {
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    let buttons: PayPalButtonsInstance | undefined;

    const renderButtons = async () => {
      for (let attempt = 0; attempt < 20 && !window.paypal && !cancelled; attempt += 1) {
        await new Promise((resolve) => window.setTimeout(resolve, 250));
      }
      if (cancelled) return;
      if (!window.paypal) {
        setError('PayPal could not load. Please use WhatsApp to request payment instead.');
        return;
      }

      buttons = window.paypal.Buttons({
        createOrder: (_data, actions) => actions.order.create({
          purchase_units: [{ description, amount: { value: amount, currency_code: 'USD' } }],
        }),
        onApprove: async (_data, actions) => {
          const orderData = await actions.order.capture();
          onSuccess(orderData.payer?.name?.given_name || 'there');
        },
        onError: () => setError('PayPal could not complete this payment. Please try again or use WhatsApp.'),
      });

      try {
        await buttons.render('#paypal-button-container');
      } catch {
        if (!cancelled) setError('PayPal could not load. Please use WhatsApp to request payment instead.');
      }
    };

    renderButtons();
    return () => {
      cancelled = true;
      void buttons?.close?.();
    };
  }, [amount, description, onSuccess]);

  return <div className="mt-5 rounded-2xl border border-[#eee5de] bg-[#fffaf6] p-4"><div className="flex items-center gap-2 text-[11px] font-bold text-[#4f7169]"><WalletCards size={15} className="text-[#5e9882]" />Pay securely with PayPal Sandbox</div><div id="paypal-button-container" className="mt-3 min-h-10" />{error && <p className="mt-2 text-[10px] leading-relaxed text-[#bd6b5d]">{error}</p>}</div>;
}

function Sessions({ booking, setBooking, bookingDate, setBookingDate, bookingTime, setBookingTime, bookingType, setBookingType, bookingSent, setBookingSent }: any) {
  const confirmBooking = () => { setBookingSent(true); setBooking(false); };
  const handlePayPalSuccess = (name: string) => { setBookingSent(true); setBooking(false); window.alert(`Transaction successful! Thank you, ${name}.`); };
  return <><section className="mt-3 rounded-[30px] bg-[#fff0e8] px-6 py-8 sm:px-10 sm:py-10"><p className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.2em] text-[#bd806d]"><CalendarDays size={14} /> Maternal education sessions</p><h1 className="mt-4 text-[31px] font-bold leading-tight tracking-[-.06em] text-[#704f4a] sm:text-[43px]">Book time for<br /><span className="text-[#df7967]">your questions.</span></h1><p className="mt-4 max-w-[560px] text-[13px] leading-relaxed text-[#98746d]">Choose a session, request a time, and the care team will confirm the secure meeting details with you.</p></section><section className="mt-6 rounded-[24px] border border-[#eee5de] bg-white p-5 sm:p-7"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><div><p className="text-[10px] font-bold uppercase tracking-[.2em] text-[#a4aaa4]">Available sessions</p><h2 className="mt-2 text-xl font-bold">Personalised support</h2></div>{bookingSent && <span className="rounded-full bg-[#eaf6ef] px-3 py-2 text-[10px] font-bold text-[#5e9882]"><Check size={12} className="mr-1 inline" />Request sent</span>}</div><div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-3">{[['Midwife check-in', '20 min', 'Questions, symptoms, next steps', MessageCircle], ['Nutrition education', '30 min', 'Supplements, hydration, meal ideas', ShoppingBag], ['Birth preparation', '45 min', 'Preferences, support, confidence', Baby]].map(([title, time, detail, Icon]) => <button key={title as string} onClick={() => { setBookingType(title as string); setBooking(true); }} className="rounded-2xl border border-[#eee5de] p-4 text-left transition hover:border-[#9bcdbb] hover:bg-[#fbfffc]"><div className="flex items-center justify-between"><div className="grid h-9 w-9 place-items-center rounded-xl bg-[#eff8f4] text-[#5e9882]">{typeof Icon === 'function' && <Icon size={16} />}</div><ArrowRight size={15} className="text-[#a4aaa4]" /></div><h3 className="mt-4 text-[13px] font-bold">{title as string}</h3><p className="mt-1 text-[10px] text-[#8c9994]">{detail as string}</p><p className="mt-3 flex items-center gap-1 text-[10px] font-bold text-[#5e9882]"><Clock3 size={12} /> {time as string}</p></button>)}</div></section>{booking && <div className="fixed inset-0 z-50 grid place-items-center bg-[#24363a]/35 p-5"><div className="w-full max-w-lg rounded-[26px] bg-white p-6 shadow-2xl"><div className="flex items-start justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.2em] text-[#a4aaa4]">Request a session</p><h2 className="mt-2 text-xl font-bold">{bookingType}</h2></div><button onClick={() => setBooking(false)}><X size={18} /></button></div><div className="mt-6 grid gap-4 sm:grid-cols-2"><label className="text-[11px] font-bold text-[#71807b]">Preferred date<input type="date" value={bookingDate} onChange={(e) => setBookingDate(e.target.value)} className="mt-2 block w-full rounded-xl border border-[#eee5de] p-3 text-sm" /></label><label className="text-[11px] font-bold text-[#71807b]">Preferred time<select value={bookingTime} onChange={(e) => setBookingTime(e.target.value)} className="mt-2 block w-full rounded-xl border border-[#eee5de] p-3 text-sm"><option>09:00</option><option>10:00</option><option>14:00</option><option>16:00</option></select></label></div><div className="mt-5 rounded-2xl bg-[#eff8f4] p-4 text-[11px] leading-relaxed text-[#4f7169]"><Video size={16} className="mr-2 inline text-[#5e9882]" />The care team will confirm whether this is a video call and send the secure meeting link through WhatsApp.</div><PayPalCheckout amount="15.00" description={bookingType} onSuccess={handlePayPalSuccess} /><div className="mt-5 grid gap-2 sm:grid-cols-2"><a href={whatsapp(`Hi, I would like to book and pay for a ${bookingType} on ${bookingDate} at ${bookingTime}. Please send the secure payment and meeting details.`)} target="_blank" rel="noreferrer" onClick={confirmBooking} className="flex items-center justify-center gap-2 rounded-xl bg-[#2f6260] py-3 text-xs font-bold text-white"><WalletCards size={14} /> Book & pay via WhatsApp</a><button onClick={() => setBooking(false)} className="rounded-xl border border-[#eee5de] py-3 text-xs font-bold text-[#71807b]">Choose later</button></div><p className="mt-4 text-[10px] leading-relaxed text-[#a4aaa4]">Payment and video links are handled by your care team; no card details are collected in this prototype.</p></div></div>}<Safety /></>;
}

function Journal({ journal, setJournal, savedJournal, setSavedJournal }: any) {
  return <><section className="mt-3 rounded-[30px] bg-[#fff0e8] px-6 py-8 sm:px-10 sm:py-10"><p className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.2em] text-[#bd806d]"><NotebookPen size={14} /> Private reflection space</p><h1 className="mt-4 text-[31px] font-bold leading-tight tracking-[-.06em] text-[#704f4a] sm:text-[43px]">Put the day<br /><span className="text-[#df7967]">somewhere gentle.</span></h1><p className="mt-4 max-w-[560px] text-[13px] leading-relaxed text-[#98746d]">Write a few words for yourself. This prototype keeps your note in the current session.</p></section><section className="mt-6 rounded-[24px] border border-[#eee5de] bg-white p-5 sm:p-7"><h2 className="text-xl font-bold">What would you like to remember?</h2><textarea value={journal} onChange={(e) => setJournal(e.target.value)} placeholder="I noticed… I needed… I’m proud that…" className="mt-6 min-h-44 w-full resize-none rounded-2xl border border-[#eee5de] bg-[#fffaf6] p-4 text-sm outline-none focus:border-[#7eb6a1]" /><div className="mt-4 flex flex-col justify-between gap-3 sm:flex-row sm:items-center"><p className="text-[10px] text-[#a4aaa4]">{journal.length}/500 characters</p><button disabled={!journal.trim()} onClick={() => { setSavedJournal(journal.trim()); setJournal(''); }} className="flex items-center justify-center gap-2 rounded-xl bg-[#2f6260] px-4 py-3 text-xs font-bold text-white disabled:opacity-40"><Plus size={15} /> Save note</button></div>{savedJournal && <div className="mt-6 rounded-2xl bg-[#eff8f4] p-4"><p className="text-[10px] font-bold uppercase tracking-[.15em] text-[#5e9882]">Saved just now</p><p className="mt-2 text-sm leading-relaxed text-[#4f6e68]">{savedJournal}</p></div>}</section></>;
}

function CareTeam({ message, setMessage, sentMessage, setSentMessage }: any) {
  return <><section className="mt-3 rounded-[30px] bg-[#eaf6f7] px-6 py-8 sm:px-10 sm:py-10"><p className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[.2em] text-[#5d9c9b]"><MessageCircle size={14} /> Your support circle</p><h1 className="mt-4 text-[31px] font-bold leading-tight tracking-[-.06em] text-[#315b5e] sm:text-[43px]">You don’t have to<br /><span className="text-[#df7967]">carry questions alone.</span></h1><p className="mt-4 max-w-[560px] text-[13px] leading-relaxed text-[#668486]">Message your care team directly or use WhatsApp for a fast, familiar handoff.</p><div className="mt-6 flex flex-wrap gap-2"><a href={whatsapp('Hi PlacentaSync care team, I would like support with: ')} target="_blank" rel="noreferrer" className="flex items-center gap-2 rounded-xl bg-[#2f6260] px-4 py-3 text-xs font-bold text-white"><MessageCircle size={15} /> Open WhatsApp</a><a href={`tel:+${WHATSAPP}`} className="flex items-center gap-2 rounded-xl border border-[#b8d7d4] bg-white px-4 py-3 text-xs font-bold text-[#397866]"><Phone size={14} /> Call +94 77 795 9386</a></div></section><div className="mt-6 grid grid-cols-1 gap-5 lg:grid-cols-2"><section className="rounded-[24px] border border-[#eee5de] bg-white p-6"><div className="flex items-center gap-3"><div className="grid h-12 w-12 place-items-center rounded-full bg-[#f2cfc3] text-xs font-bold text-[#8c5c52]">SM</div><div><h2 className="text-[16px] font-bold">Sarah Mitchell</h2><p className="text-[11px] text-[#8c9994]">Midwife · Your care team</p></div>  <span className="ml-auto h-2.5 w-2.5 rounded-full bg-[#71c197]" /></div><div className="mt-6 rounded-2xl bg-[#eff8f4] p-4 text-[11px] leading-relaxed text-[#4f7169]">“I’m here to help you prepare questions and understand your next steps.”</div></section><section className="rounded-[24px] border border-[#eee5de] bg-white p-6"><p className="text-[10px] font-bold uppercase tracking-[.2em] text-[#a4aaa4]">New message</p><h2 className="mt-2 text-[20px] font-bold">What would you like to share?</h2><textarea value={message} onChange={(e) => setMessage(e.target.value)} placeholder="For example: I have a question about my next appointment…" className="mt-5 min-h-32 w-full resize-none rounded-2xl border border-[#eee5de] bg-[#fffaf6] p-4 text-sm outline-none focus:border-[#7eb6a1]" /><button disabled={!message.trim()} onClick={() => { setSentMessage(message.trim()); setMessage(''); }} className="mt-4 flex items-center gap-2 rounded-xl bg-[#2f6260] px-4 py-3 text-xs font-bold text-white disabled:opacity-40"><Send size={14} /> Save message</button>{sentMessage && <div className="mt-5 flex gap-2 rounded-2xl bg-[#eaf6ef] p-4 text-[11px] leading-relaxed text-[#4f7169]"><CheckCircle2 size={16} className="shrink-0 text-[#5e9882]" />Message saved. In a connected version, your care team would receive it.</div>}</section></div><Safety /></>;
}

function Safety() { return <footer className="mx-auto mt-8 flex max-w-2xl items-start gap-2 text-center text-[10px] leading-relaxed text-[#a2aaa5]"><CircleHelp size={13} className="mt-0.5 shrink-0" />PlacentaSync is a support and communication tool, not a medical diagnosis. For urgent symptoms, contact your clinician or local emergency services.</footer>; }

export default App;
