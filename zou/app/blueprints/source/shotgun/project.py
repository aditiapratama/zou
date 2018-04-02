from flask_restful import current_app

from zou.app.models.project import Project
from zou.app.models.project_status import ProjectStatus

from zou.app.services import file_tree_service, projects_service

from zou.app.blueprints.source.shotgun.base import (
    BaseImportShotgunResource,
    ImportRemoveShotgunBaseResource
)


class ImportShotgunProjectsResource(BaseImportShotgunResource):

    def __init__(self):
        BaseImportShotgunResource.__init__(self)

    def prepare_import(self):
        self.project_status_names = self.extract_status_names(self.sg_entries)
        projects_service.save_project_status(self.project_status_names)
        self.project_status_map = ProjectStatus.get_id_map(field="name")

    def extract_status_names(self, sg_projects):
        return {x["sg_status"] for x in sg_projects}

    def extract_data(self, sg_project):
        sg_project_status = sg_project["sg_status"]
        sg_fps = sg_project.get("sg_fps", None)
        sg_width___height = sg_project.get("sg_width___height", None)
        project_status_id = self.project_status_map.get(sg_project_status, None)

        data = {
            "project_status_id": project_status_id,
            "name": sg_project["name"],
            "shotgun_id": sg_project["id"],
            "data": {}
        }

        if sg_fps is not None:
            data["data"]["fps"] = sg_fps

        if sg_width___height is not None:
            data["data"]["width_height"] = sg_width___height

        return data

    def import_entry(self, data):
        project = Project.get_by(shotgun_id=data["shotgun_id"])

        if project is None:
            project = Project(**data)

            tree_name = current_app.config["DEFAULT_FILE_TREE"]
            project.file_tree = file_tree_service.get_tree_from_file(tree_name)

            project.save()
            current_app.logger.info("Project created: %s" % project)

        else:
            project.update(data)
            current_app.logger.info("Project updated: %s" % project)

        return project


class ImportRemoveShotgunProjectResource(ImportRemoveShotgunBaseResource):

    def __init__(self):
        ImportRemoveShotgunBaseResource.__init__(self, Project)