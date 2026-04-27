import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";

type QuickStatProps = {
  icon: LucideIcon;
  label: string;
  value: string;
  hint: string;
};

export function QuickStat({ icon: Icon, label, value, hint }: QuickStatProps): React.JSX.Element {
  return (
    <Card className="border-border/70 bg-card/85 shadow-sm">
      <CardContent className="flex items-start justify-between gap-4 pt-6">
        <div className="space-y-1">
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{label}</p>
          <p className="text-2xl font-semibold text-foreground">{value}</p>
          <p className="text-sm text-muted-foreground">{hint}</p>
        </div>
        <div className="flex size-10 items-center justify-center rounded-2xl bg-primary/10 text-primary">
          <Icon className="size-5" />
        </div>
      </CardContent>
    </Card>
  );
}
