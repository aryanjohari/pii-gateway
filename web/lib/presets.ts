// Fictional data. Each value passes the gateway's checks so the NZ recognisers fire; verified
// against config.demo-nz.yaml when written.
export type Preset = { id: string; label: string; text: string };

export const PRESETS: Preset[] = [
  {
    id: "clinic",
    label: "Clinic note (NHI)",
    text: "Clinic note, 12 March: Sarah Thompson attended with a sore knee. NHI ZAC5361. Please call 09 912 4200 to book a follow-up.",
  },
  {
    id: "invoice",
    label: "Invoice (IRD number)",
    text: "Invoice 1042, due 30 April. Contractor: Liam Walker, IRD number 180743146. Payment queries: accounts@example.co.nz.",
  },
  {
    id: "email",
    label: "Email (driver licence)",
    text: "Hi Priya, please send a copy of your driver licence AB123456 to hr@example.co.nz so we can finish your onboarding. Thanks, Tom Baker",
  },
];
