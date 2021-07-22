# Copyright 2021 ForgeFlow S.L.  <https://www.forgeflow.com>
# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


def map_project_project_rating_status(env):
    openupgrade.map_values(
        env.cr,
        openupgrade.get_legacy_name("rating_status"),
        "rating_status",
        [("no", "stage")],
        table="project_project",
    )


def _fill_res_users_m2m_tables(env):
    # TODO: Take into account channels and task followers part of the old rule
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO project_allowed_internal_users_rel
        (project_project_id, res_users_id)
        SELECT pp.id, ru.id
        FROM project_project pp
        JOIN mail_followers mf ON mf.res_model = 'project.project' AND mf.res_id = pp.id
        JOIN res_users ru ON ru.partner_id = mf.partner_id AND NOT ru.share
        WHERE pp.privacy_visibility = 'followers'
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO project_allowed_portal_users_rel
        (project_project_id, res_users_id)
        SELECT pp.id, ru.id
        FROM project_project pp
        JOIN mail_followers mf ON mf.res_model = 'project.project' AND mf.res_id = pp.id
        JOIN res_partner rp ON mf.partner_id = rp.id
            OR mf.partner_id = rp.commercial_partner_id
        JOIN res_users ru ON ru.partner_id = rp.id AND ru.share
        WHERE pp.privacy_visibility = 'portal'
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        INSERT INTO project_task_res_users_rel
        (project_task_id, res_users_id)
        SELECT pt.id, rel.res_users_id
        FROM project_allowed_internal_users_rel rel
        JOIN project_task pt ON pt.project_id = rel.project_project_id
        UNION
        SELECT pt.id, rel.res_users_id
        FROM project_allowed_portal_users_rel rel
        JOIN project_task pt ON pt.project_id = rel.project_project_id
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    map_project_project_rating_status(env)
    _fill_res_users_m2m_tables(env)
    openupgrade.load_data(env.cr, "project", "14.0.1.1/noupdate_changes.xml")
    openupgrade.delete_records_safely_by_xml_id(
        env,
        [
            "project.msg_task_4",
            "project.project_task_data_0",
            "project.project_task_data_1",
            "project.project_task_data_11",
            "project.project_task_data_12",
            "project.project_task_data_13",
            "project.project_task_data_14",
            "project.project_task_data_2",
            "project.project_task_data_4",
            "project.project_task_data_5",
            "project.project_task_data_6",
            "project.project_task_data_7",
            "project.project_task_data_9",
            "project.project_stage_data_0",
            "project.project_stage_data_1",
            "project.project_stage_data_2",
            # We do this at the end for assuring not having this records assigned on the
            # rest of the demo data
            "project.project_project_data",
            "project.project_tag_data",
        ],
    )
    openupgrade.delete_record_translations(
        env.cr,
        "project",
        ["mail_template_data_project_task", "rating_project_request_email_template"],
    )
