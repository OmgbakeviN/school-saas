import {
  BookOpen,
  BriefcaseBusiness,
  GraduationCap,
  Mail,
  MapPin,
  Phone,
  UserRound,
  UsersRound,
} from "lucide-react";

import Dialog from "../../components/Dialog";
import SchoolIdentity from "../../components/SchoolIdentity";
import { useI18n } from "../../i18n";

function Detail({ label, value, icon: Icon }) {
  if (value === null || value === undefined || value === "") return null;

  return (
    <div
      className="rounded-2xl border bg-white/90 p-3.5 shadow-sm"
      style={{ borderColor: "rgb(var(--school-primary-rgb) / 0.14)" }}
    >
      <div className="flex items-center gap-2 text-xs font-medium text-slate-500">
        {Icon && (
          <Icon
            size={14}
            style={{ color: "var(--school-primary)" }}
          />
        )}
        {label}
      </div>
      <div className="mt-1.5 break-words text-sm font-medium text-slate-800">
        {value}
      </div>
    </div>
  );
}

function initials(person) {
  return `${person?.first_name?.[0] || ""}${person?.last_name?.[0] || ""}`.toUpperCase();
}

function StudentProfile({ person, t }) {
  const enrollment = person.current_enrollment;
  const guardians = person.guardians || [];

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Detail label={t("people.students.matricule")} value={person.matricule} icon={GraduationCap} />
        <Detail label={t("people.students.gender")} value={person.gender ? t(`people.gender.${person.gender.toLowerCase()}`) : "—"} />
        <Detail label={t("people.students.birthDate")} value={person.date_of_birth || "—"} />
        <Detail label={t("people.students.birthPlace")} value={person.place_of_birth || "—"} />
        <Detail label={t("people.students.nationality")} value={person.nationality || "—"} />
        <Detail label={t("people.students.admissionDate")} value={person.admission_date || "—"} />
        <Detail label={t("people.fields.phone")} value={person.phone || "—"} icon={Phone} />
        <Detail label={t("people.fields.email")} value={person.email || "—"} icon={Mail} />
        <Detail label={t("people.fields.address")} value={person.address || "—"} icon={MapPin} />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-900">
          {t("people.profile.currentEnrollment")}
        </h3>
        <div className="mt-2 rounded-2xl border border-slate-200 p-4 text-sm">
          {enrollment ? (
            <div className="flex flex-wrap gap-x-5 gap-y-2">
              <span><b>{t("people.enrollments.classroom")}:</b> {enrollment.classroom_name}</span>
              <span><b>{t("people.enrollments.year")}:</b> {enrollment.academic_year_name}</span>
            </div>
          ) : (
            <span className="text-slate-500">{t("people.students.notEnrolled")}</span>
          )}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-slate-900">
          {t("people.profile.guardians")}
        </h3>
        <div className="mt-2 space-y-2">
          {!guardians.length && (
            <div className="rounded-2xl border border-dashed border-slate-300 p-4 text-sm text-slate-500">
              {t("people.profile.noGuardians")}
            </div>
          )}
          {guardians.map((guardian) => (
            <div key={guardian.link_id} className="rounded-2xl border border-slate-200 p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <div className="font-medium">{guardian.name}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {guardian.phone || "—"} • {guardian.relationship_label}
                  </div>
                </div>
                {guardian.is_primary && (
                  <span className="tenant-primary-soft tenant-primary-text rounded-full px-2.5 py-1 text-xs font-medium">
                    {t("people.guardians.primaryShort")}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {person.notes && (
        <Detail label={t("people.fields.notes")} value={person.notes} />
      )}
    </div>
  );
}

function TeacherProfile({ person, t }) {
  const account = person.linked_account;
  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Detail label={t("people.teachers.employeeNumber")} value={person.employee_number} icon={UserRound} />
        <Detail label={t("people.teachers.speciality")} value={person.speciality || "—"} icon={BriefcaseBusiness} />
        <Detail label={t("people.teachers.hireDate")} value={person.hire_date || "—"} />
        <Detail label={t("people.fields.phone")} value={person.phone || "—"} icon={Phone} />
        <Detail label={t("people.fields.email")} value={person.email || "—"} icon={Mail} />
        <Detail label={t("people.teachers.status")} value={person.status} />
      </div>

      <div>
        <h3 className="text-sm font-semibold">{t("people.profile.loginAccount")}</h3>
        <div className="mt-2 rounded-2xl border border-slate-200 p-4 text-sm text-slate-600">
          {account ? (
            <>
              <div className="font-medium text-slate-900">
                {[account.first_name, account.last_name].filter(Boolean).join(" ") || account.email}
              </div>
              <div className="mt-1">{account.email}</div>
            </>
          ) : t("people.profile.noLoginAccount")}
        </div>
      </div>

      {person.notes && <Detail label={t("people.fields.notes")} value={person.notes} />}
    </div>
  );
}

function GuardianProfile({ person, t }) {
  const children = person.children || [];
  const account = person.linked_account;

  return (
    <div className="space-y-5">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Detail label={t("people.fields.phone")} value={person.phone} icon={Phone} />
        <Detail label={t("people.guardians.alternatePhone")} value={person.alternate_phone || "—"} icon={Phone} />
        <Detail label={t("people.fields.email")} value={person.email || "—"} icon={Mail} />
        <Detail label={t("people.guardians.occupation")} value={person.occupation || "—"} icon={BriefcaseBusiness} />
        <Detail label={t("people.fields.address")} value={person.address || "—"} icon={MapPin} />
        <Detail label={t("people.guardians.preferredLanguage")} value={person.preferred_language || "—"} />
      </div>

      <div>
        <div className="flex items-center justify-between gap-3">
          <h3 className="text-sm font-semibold text-slate-900">
            {t("people.profile.children")}
          </h3>
          <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-600">
            {children.length}
          </span>
        </div>
        <div className="mt-2 space-y-2">
          {!children.length && (
            <div className="rounded-2xl border border-dashed border-slate-300 p-4 text-sm text-slate-500">
              {t("people.profile.noChildren")}
            </div>
          )}
          {children.map((child) => (
            <div key={child.link_id} className="rounded-2xl border border-slate-200 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="font-medium text-slate-900">{child.name}</div>
                  <div className="mt-1 text-xs text-slate-500">
                    {child.matricule}
                    {child.classroom ? ` • ${child.classroom}` : ""}
                    {child.academic_year ? ` • ${child.academic_year}` : ""}
                  </div>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">
                    {child.relationship_label}
                  </span>
                  {child.is_primary && (
                    <span className="tenant-primary-soft tenant-primary-text rounded-full px-2.5 py-1 text-xs font-medium">
                      {t("people.guardians.primaryShort")}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold">{t("people.profile.loginAccount")}</h3>
        <div className="mt-2 rounded-2xl border border-slate-200 p-4 text-sm text-slate-600">
          {account ? account.email : t("people.profile.noLoginAccount")}
        </div>
      </div>
    </div>
  );
}

export default function PersonProfileDialog({ open, type, person, school, onClose }) {
  const { t } = useI18n();
  if (!person) return null;

  const title = `${person.last_name || ""} ${person.first_name || ""}`.trim();
  const typeLabel = t(`people.profile.types.${type}`);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      title={t("people.profile.title")}
      description={typeLabel}
      maxWidth="max-w-4xl"
    >
      <div
        className="mb-5 overflow-hidden rounded-3xl border shadow-sm"
        style={{
          borderColor: "rgb(var(--school-primary-rgb) / 0.20)",
          background:
            "linear-gradient(135deg, rgb(var(--school-primary-rgb) / 0.12), rgb(var(--school-secondary-rgb) / 0.08), rgba(255,255,255,0.96))",
        }}
      >
        <div
          className="h-1.5"
          style={{
            background:
              "linear-gradient(90deg, var(--school-primary), var(--school-secondary))",
          }}
        />
        <div className="border-b border-white/70 bg-white/55 px-5 py-3 backdrop-blur-sm">
          <SchoolIdentity school={school} compact />
        </div>

        <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center">
          {type === "student" && person.photo_url ? (
            <img
              src={person.photo_url}
              alt={title}
              className="h-24 w-24 shrink-0 rounded-3xl border-4 border-white object-cover shadow-md"
              style={{
                boxShadow:
                  "0 10px 28px rgb(var(--school-primary-rgb) / 0.16)",
              }}
            />
          ) : (
            <div
              className="grid h-24 w-24 shrink-0 place-items-center rounded-3xl border-4 border-white text-2xl font-semibold shadow-md"
              style={{
                background: "rgb(var(--school-primary-rgb) / 0.10)",
                color: "var(--school-primary)",
                boxShadow:
                  "0 10px 28px rgb(var(--school-primary-rgb) / 0.16)",
              }}
            >
              {initials(person)}
            </div>
          )}

          <div className="min-w-0">
            <div
              className="text-xs font-semibold uppercase tracking-[0.18em]"
              style={{ color: "var(--school-primary)" }}
            >
              {typeLabel}
            </div>
            <h2 className="mt-1 text-2xl font-semibold tracking-tight text-slate-950">
              {title}
            </h2>
            <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-600">
              {type === "student" &&
                person.current_enrollment?.classroom_name && (
                  <span
                    className="rounded-full border bg-white/90 px-3 py-1.5"
                    style={{
                      borderColor:
                        "rgb(var(--school-primary-rgb) / 0.16)",
                    }}
                  >
                    {person.current_enrollment.classroom_name}
                  </span>
                )}
              {type === "guardian" && (
                <span
                  className="rounded-full border bg-white/90 px-3 py-1.5"
                  style={{
                    borderColor:
                      "rgb(var(--school-primary-rgb) / 0.16)",
                  }}
                >
                  {person.children_count || 0}{" "}
                  {t("people.guardians.children")}
                </span>
              )}
              {person.status && (
                <span
                  className="rounded-full border bg-white/90 px-3 py-1.5"
                  style={{
                    borderColor:
                      "rgb(var(--school-primary-rgb) / 0.16)",
                  }}
                >
                  {person.status}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {type === "student" && <StudentProfile person={person} t={t} />}
      {type === "teacher" && <TeacherProfile person={person} t={t} />}
      {type === "guardian" && <GuardianProfile person={person} t={t} />}
    </Dialog>
  );
}
