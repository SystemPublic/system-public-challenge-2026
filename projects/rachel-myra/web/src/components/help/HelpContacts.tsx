import { Button } from "@/components/ui/button";
import { Placeholder } from "@/components/Placeholder";
import type { HelpContact } from "@/lib/helpContacts";

export function HelpContacts({ contacts, lang, sourceFile }: { contacts: HelpContact[]; lang: "en" | "es"; sourceFile: string }) {
  const es = lang === "es";
  const title = es ? "¿Necesita ayuda con la comida o los mandados?" : "Need help with groceries or errands?";
  if (!contacts.length) return <Placeholder title={title}>Data goes here: {sourceFile}</Placeholder>;
  return (
    <section className="space-y-4 rounded-lg border border-border bg-card p-4 text-lg">
      <h2 className="text-patient-lg font-semibold tracking-tight">{title}</h2>
      <ul className="space-y-4">
        {contacts.map((c) => (
          <li key={c.id} className="space-y-1">
            <p className="font-semibold">{c.name}</p>
            {c.offers && <p className="text-muted-foreground">{c.offers}</p>}
            <p className="text-muted-foreground">{es ? `a unas ${c.distanceMi} millas` : `about ${c.distanceMi} mi away`}</p>
            {c.address && <p>{c.address}</p>}
            {c.phone ? (
              <Button asChild className="mt-1 min-h-12 w-full text-lg">
                <a href={`tel:${c.phone.replace(/[^\d+]/g, "")}`}>{es ? "Llamar" : "Call"} {c.phone}</a>
              </Button>
            ) : c.website ? (
              <Button asChild variant="outline" className="mt-1 min-h-12 w-full text-lg">
                <a href={c.website} target="_blank" rel="noreferrer">{es ? "Ver sitio web" : "Visit website"}</a>
              </Button>
            ) : null}
          </li>
        ))}
      </ul>
      <div className="space-y-1">
        <p className="font-semibold">{es ? "¿No sabe a quién llamar?" : "Not sure who to call?"}</p>
        <p className="text-muted-foreground">
          {es
            ? "Llame al 311 (línea de servicios de la Ciudad de Nueva York) y pida ayuda con comida o mandados."
            : "Call 311 (New York City's services line) and ask for help with food or errands."}
        </p>
        <Button asChild size="lg" className="h-14 w-full text-lg">
          <a href="tel:311">{es ? "Llamar al 311" : "Call 311"}</a>
        </Button>
      </div>
      <p className="text-base text-muted-foreground">{es ? "Los horarios y servicios pueden cambiar. Llame antes." : "Hours and services can change. Call ahead."}</p>
    </section>
  );
}
