node('maven') {

    def appName="python-http-producer"
    def projectName="testpy"
    def repoUrl="github.com/socrates965/python-http-producer.git"
    def branchName="main"
    
    def pullImageDC="quayuser-djbc-dc-pull-secret"
    def pullImageDRC="quayuser-djbc-drc-pull-secret"

    def intRegistryDev="default-route-openshift-image-registry.apps.dev.customs.go.id"
    def extRegistryQuayDC="quay-registry.apps.proddc.customs.go.id"
    def extRegistryQuayDRC="quay-registry.apps.proddrc.customs.go.id"
    def extRegistryHrbrDC="dc01w01hrbr.customs.go.id"
    def extRegistryHrbrDRC="drc01dev01hrbr.customs.go.id"

    stage ('Git Clone') {
        sh "git config --global http.sslVerify false"
        sh "git clone https://${repoUrl} source "
    }
    
    stage ('App Build') {
        dir("source") {
            sh "git fetch"
            sh "git switch ${branchName}" 
            }

        }

    stage ('App Push') {
        dir("source") {
            sh "mkdir -p build-folder/target/ build-folder/apps/ "
            sh "cp dockerfile build-folder/Dockerfile"
            sh "cp main.py build-folder/main.py"
            sh "cp requirements.txt build-folder/requirements.txt"
            sh "cp CustomLogger.py build-folder/CustomLogger.py"

            def tag = sh(returnStdout: true, script: "git rev-parse --short=8 HEAD").trim();
            def tokenLocal = sh(script: 'oc whoami -t', returnStdout: true).trim()
            
            //sh "oc delete bc ${appName}"
            sh "cat build-folder/Dockerfile | oc new-build -D - --name ${appName} || true"
            sh "oc start-build ${appName} --from-dir=build-folder/. --follow --wait "
            //sleep(time:600,unit:"SECONDS")
            //NEW SECTION BELOW//
            sh "oc tag cicd4/${appName}:latest ${projectName}/${appName}:${tag} "
            sh "echo 'COMMIT ID ${tag}'"
            
            sh "oc registry login --skip-check"
            
            //QUAY FORMAT <registry>/djbc/<namespace>_<deployment_name>
            
            withCredentials([usernamePassword(credentialsId: 'quay-dc-credential', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]){
                sh "skopeo copy --remove-signatures  --src-creds=jenkins:${tokenLocal} --src-tls-verify=false docker://${intRegistryDev}/${projectName}/${appName}:${tag} docker://${extRegistryQuayDC}/djbc/${projectName}_${appName}-dev:${tag} --dest-creds \${USERNAME}:\${PASSWORD} --dest-tls-verify=false"
                sh "oc tag cicd4/${appName}:latest ${projectName}/${appName}:latest "
                sh "skopeo copy --remove-signatures  --src-creds=jenkins:${tokenLocal} --src-tls-verify=false docker://${intRegistryDev}/${projectName}/${appName}:latest docker://${extRegistryQuayDC}/djbc/${projectName}_${appName}-dev:latest --dest-creds \${USERNAME}:\${PASSWORD} --dest-tls-verify=false"
            }

            // withCredentials([usernamePassword(credentialsId: 'quay-drc-credential', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]){
            //     sh "skopeo copy --remove-signatures  --src-creds=jenkins:${tokenLocal} --src-tls-verify=false docker://${intRegistryDev}/${projectName}/${appName}:${tag} docker://${extRegistryQuayDRC}/djbc/${projectName}_${appName}-dev:${tag} --dest-creds \${USERNAME}:\${PASSWORD} --dest-tls-verify=false"
            //     sh "oc tag cicd4/${appName}:latest ${projectName}/${appName}:latest "
            //     sh "skopeo copy --remove-signatures  --src-creds=jenkins:${tokenLocal} --src-tls-verify=false docker://${intRegistryDev}/${projectName}/${appName}:latest docker://${extRegistryQuayDRC}/djbc/${projectName}_${appName}-dev:latest --dest-creds \${USERNAME}:\${PASSWORD} --dest-tls-verify=false"
            // }
        }
    }
 
    stage('Deploy to Dev') {
        parallel (
            "App Deploy to DEV DC OCP": {
                dir("source") {
                    sh "cp kubernetes-dev.yaml kubernetes-dc.yaml"
                    sh "oc  apply -f quayuser-djbc-dc-pull-secret.yaml -n ${projectName}"
                    sh "sed 's,\\\$REGISTRY/\\\$HARBOR_NAMESPACE/\\\$APP_NAME:\\\$BUILD_NUMBER,${extRegistryQuayDC}/djbc/${projectName}_${appName}-dev:latest,g' kubernetes-dc.yaml > kubernetes-dc-quay.yaml"
                    sh "sed 's,\\\$IMAGEPULLSECRET,${pullImageDC},g' kubernetes-dc-quay.yaml > kubernetes-ocp-quay-dc.yaml"
                    sh "oc apply -f kubernetes-ocp-quay-dc.yaml -n ${projectName}"
                    sh "oc set triggers deployment/${appName} -c ${appName} -n ${projectName} || true "
                    sh "oc rollout restart deployment/${appName} -n ${projectName}"
                }
            }

            // "App Deploy to DEV DRC OCP": {
            //     dir("source") {
            //         withCredentials([file(credentialsId: 'drc-dev-ocp', variable: 'KUBE_CONFIG_DEV_DRC')]) {
            //             sh "cp kubernetes-dev.yaml kubernetes-drc.yaml"
            //             sh "oc --kubeconfig=\$KUBE_CONFIG_DEV_DRC apply -f quayuser-djbc-drc-pull-secret.yaml -n ${projectName}"
            //             sh "sed 's,\\\$REGISTRY/\\\$HARBOR_NAMESPACE/\\\$APP_NAME:\\\$BUILD_NUMBER,${extRegistryQuayDRC}/djbc/${projectName}_${appName}-dev:latest,g' kubernetes-drc.yaml > kubernetes-drc-quay.yaml"
            //             sh "sed 's,\\\$IMAGEPULLSECRET,${pullImageDRC},g' kubernetes-drc-quay.yaml > kubernetes-ocp-quay-drc.yaml"
            //             sh "oc --kubeconfig=\$KUBE_CONFIG_DEV_DRC apply -f kubernetes-ocp-quay-drc.yaml -n ${projectName}"
            //             sh "oc --kubeconfig=\$KUBE_CONFIG_DEV_DRC set triggers deployment/${appName} -c ${appName} -n ${projectName} || true "
            //             sh "oc --kubeconfig=\$KUBE_CONFIG_DEV_DRC rollout restart deployment/${appName} -n ${projectName}"
            //         }
            //     }
            // }
        )
    }
}
