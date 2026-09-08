const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"];
const dayOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

interface TimetableItem {
  day: string;
  period: string;
  course?: string;
  lecturer?: string;
  room?: string;
  [key: string]: any;
}

interface Props {
  data: TimetableItem[];
  timetableType?: "course" | "exam";
}

function parsePeriod(period: string) {
  const normalized = period.trim();
  const parts = normalized.split("-").map((p) => p.trim());
  if (parts.length !== 2) return null;

  const parseTime = (time: string) => {
    const cleaned = time.replace(/\s+/g, "").replace(/:00$/, "");
    const [hourStr, minuteStr] = cleaned.split(":");
    const hour = parseInt(hourStr, 10);
    const minute = minuteStr ? parseInt(minuteStr, 10) : 0;
    if (Number.isNaN(hour) || Number.isNaN(minute)) return null;
    return hour * 60 + minute;
  };

  const start = parseTime(parts[0]);
  const end = parseTime(parts[1]);
  if (start === null || end === null) return null;
  return { start, end };
}

function parseTimeValue(timeStr: string) {
  const cleaned = timeStr.trim().replace(/\s+/g, "").replace(/:00$/, "");
  const [hourStr, minuteStr] = cleaned.split(":");
  const hour = parseInt(hourStr, 10);
  const minute = minuteStr ? parseInt(minuteStr, 10) : 0;
  if (Number.isNaN(hour) || Number.isNaN(minute)) return null;
  return hour * 60 + minute;
}

function getExamRowRanges() {
  return [
    { label: "7:00-10:00", start: 7 * 60, end: 10 * 60 },
    { label: "11:00-14:00", start: 11 * 60, end: 14 * 60 },
    { label: "15:00-18:00", start: 15 * 60, end: 18 * 60 },
  ];
}

function formatMinutes(minutes: number) {
  const hour = Math.floor(minutes / 60);
  const minute = minutes % 60;
  return `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`;
}

function normalizePeriod(period: string) {
  const parsed = parsePeriod(period);
  if (!parsed) return period.trim();
  return `${formatMinutes(parsed.start)}-${formatMinutes(parsed.end)}`;
}

function getDisplayPeriods(data: TimetableItem[], isExamTimetable: boolean) {
  if (isExamTimetable) {
    return getExamRowRanges().map((range) => range.label);
  }

  const uniquePeriods = Array.from(
    new Set(
      data
        .map((item) => item.period)
        .filter(Boolean)
        .map((period) => normalizePeriod(period))
    )
  ) as string[];

  const sortedPeriods = uniquePeriods
    .map((period) => ({ period, parsed: parsePeriod(period) }))
    .filter((item) => item.parsed !== null)
    .sort((a, b) => (a.parsed!.start - b.parsed!.start))
    .map((item) => item.period);

  // For course timetables, add breaks between gaps
  const displayPeriods: string[] = [];
  for (let i = 0; i < sortedPeriods.length; i++) {
    const current = sortedPeriods[i];
    displayPeriods.push(current);

    const currentParsed = parsePeriod(current);
    const nextParsed = sortedPeriods[i + 1] ? parsePeriod(sortedPeriods[i + 1]) : null;
    if (currentParsed && nextParsed && nextParsed.start > currentParsed.end) {
      displayPeriods.push(`${formatMinutes(currentParsed.end)}-${formatMinutes(nextParsed.start)}`);
    }
  }

  return displayPeriods;
}

function isExamItemInRange(item: TimetableItem, range: { start: number; end: number }) {
  const timeValue = item.period || item.time || "";
  const minutes = parseTimeValue(String(timeValue));
  if (minutes === null) return false;
  return minutes >= range.start && minutes <= range.end;
}

export default function TimetableGrid({ data, timetableType = "course" }: Props) {
  if (!data || !Array.isArray(data) || data.length === 0) {
    return <div className="timetable-empty">No timetable data available</div>;
  }

  const isExamTimetable = timetableType === "exam";
  const periods = getDisplayPeriods(data, isExamTimetable);
  const daysToDisplay = isExamTimetable
    ? Array.from(new Set(data.map((item) => item.day).filter(Boolean))).sort((a, b) => {
        const aIndex = dayOrder.indexOf(a);
        const bIndex = dayOrder.indexOf(b);
        if (aIndex === -1 && bIndex === -1) {
          return a.localeCompare(b);
        }
        if (aIndex === -1) {
          return 1;
        }
        if (bIndex === -1) {
          return -1;
        }
        return aIndex - bIndex;
      })
    : days;

  const getCell = (day: string, period: string) => {
    if (isExamTimetable) {
      const ranges = getExamRowRanges();
      const targetRange = ranges.find((range) => range.label === period);
      if (!targetRange) {
        return [];
      }
      return data.filter(
        (item) => item.day === day && isExamItemInRange(item, targetRange)
      );
    }

    return data.filter(
      (item) => item.day === day && normalizePeriod(item.period) === normalizePeriod(period)
    );
  };

  const isBreakRow = (period: string) => {
    if (isExamTimetable) {
      return false;
    }
    return data.every((item) => normalizePeriod(item.period) !== normalizePeriod(period));
  };

  return (
    <table>
      <thead>
        <tr>
          <th>Time</th>
          {daysToDisplay.map((d) => (
            <th key={d}>{d}</th>
          ))}
        </tr>
      </thead>

      <tbody>
        {periods.map((p) => {
          const breakRow = isBreakRow(p);
          return (
            <tr key={p} className={breakRow ? "break-row" : undefined}>
              <td><b>{p}</b></td>

              {daysToDisplay.map((d) => {
                const classes = getCell(d, p);

                return (
                  <td key={d}>
                    {classes.length > 0 ? (
                      classes.map((c, i) => (
                        <div key={i} className="class-cell">
                          <b>{c.course || "N/A"}</b><br />
                          {c.lecturer || "No lecturer"}<br />
                          {c.room || "No room"}
                        </div>
                      ))
                    ) : breakRow ? (
                      <span className="break-cell">Break</span>
                    ) : (
                      <span className="empty-cell">-</span>
                    )}
                  </td>
                );
              })}
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}