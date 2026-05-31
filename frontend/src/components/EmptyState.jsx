import { Inbox } from "lucide-react";

export default function EmptyState({ message = "Nothing here yet.", icon: Icon = Inbox, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-slate-500">
      <Icon className="w-10 h-10 mb-3 opacity-40" />
      <p className="text-sm">{message}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
