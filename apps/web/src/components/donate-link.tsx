const KO_FI_URL = "https://ko-fi.com/berrybrain";

export function DonateLink() {
  return (
    <a
      href={KO_FI_URL}
      target="_blank"
      rel="noopener noreferrer"
      className="bb-action fixed bottom-4 right-4 z-[70] inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold"
      aria-label="Donate to BerryBrain on Ko-fi"
    >
      <span aria-hidden="true">♥</span>
      {" Donate"}
    </a>
  );
}
