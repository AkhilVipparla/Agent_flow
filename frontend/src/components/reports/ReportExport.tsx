import { Button } from '../ui/Button';

interface Props {
  content: string;
  filename?: string;
}

export function ReportExport({ content, filename = 'report' }: Props) {
  const handleExport = () => {
    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Button size="sm" variant="secondary" onClick={handleExport}>
      Export .md
    </Button>
  );
}
